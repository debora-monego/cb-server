# app/jobs/forms.py

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
    StringField, SelectField, FloatField, BooleanField, 
    TextAreaField, IntegerField, HiddenField
)
from wtforms.validators import (
    DataRequired, Optional, NumberRange, ValidationError, 
    Length, Regexp
)
from app.models.jobs import JobType
from app.utils.validators import validate_fasta_sequence
import json
import os

class BaseJobForm(FlaskForm):
    """Base form for all job types."""
    job_type = SelectField(
        'Job Type',
        choices=[(jt.value, jt.value.replace('_', ' ').title()) 
                for jt in JobType],
        validators=[DataRequired()]
    )
    description = StringField(
        'Job Description',
        validators=[
            DataRequired(),
            Length(max=120, message="Description must be less than 120 characters")
        ],
        description="A brief description of this job"
    )

class MoleculeJobForm(BaseJobForm):
    """Form for molecule generation jobs."""
    species_template = SelectField(
        'Species Template',
        choices=[
            ('human', 'Human Collagen Type I'),
            ('mouse', 'Mouse Collagen Type I'),
            ('rat', 'Rat Collagen Type I'),
            ('custom', 'Custom FASTA Sequence')
        ],
        validators=[DataRequired()],
        description="Select a species template or upload custom sequence"
    )
    
    custom_fasta = FileField(
        'Custom FASTA File',
        validators=[
            FileAllowed(['fasta', 'fa'], 'FASTA files only!'),
            Optional()
        ],
        description="Upload a FASTA file containing your sequence"
    )
    
    # Crosslink configuration
    n_terminal_crosslink = SelectField(
        'N-terminal Crosslink',
        choices=[
            ('none', 'None'),
            ('hydroxylysine', 'Hydroxylysine'),
            ('custom', 'Custom')
        ],
        validators=[Optional()],
        default='none'
    )
    
    c_terminal_crosslink = SelectField(
        'C-terminal Crosslink',
        choices=[
            ('none', 'None'),
            ('hydroxylysine', 'Hydroxylysine'),
            ('custom', 'Custom')
        ],
        validators=[Optional()],
        default='none'
    )
    
    n_terminal_position = StringField(
        'N-terminal Position',
        validators=[Optional(), Regexp(r'^\d+$', message="Must be a number")],
        description="Position for N-terminal crosslink"
    )
    
    c_terminal_position = StringField(
        'C-terminal Position',
        validators=[Optional(), Regexp(r'^\d+$', message="Must be a number")],
        description="Position for C-terminal crosslink"
    )
    
    def validate_custom_fasta(self, field):
        """Validate custom FASTA file if selected."""
        if self.species_template.data == 'custom':
            if not field.data:
                raise ValidationError('Please upload a FASTA file for custom sequence')
            if field.data:
                try:
                    content = field.data.read().decode('utf-8')
                    field.data.seek(0)  # Reset file pointer
                    validate_fasta_sequence(content)
                except Exception as e:
                    raise ValidationError(f'Invalid FASTA format: {str(e)}')

class FibrilJobForm(BaseJobForm):
    """Form for fibril generation jobs."""
    molecule_source = SelectField(
        'Molecule Source',
        choices=[
            ('existing', 'Use Existing Molecule'),
            ('upload', 'Upload Molecule File'),
            ('new', 'Generate New Molecule')
        ],
        validators=[DataRequired()],
        description="Select source for collagen molecules"
    )
    
    existing_molecule_id = SelectField(
        'Existing Molecule',
        choices=[],  # Populated dynamically
        validators=[Optional()],
        coerce=int,
        description="Select a previously generated molecule"
    )
    
    molecule_file = FileField(
        'Molecule PDB File',
        validators=[
            FileAllowed(['pdb'], 'PDB files only!'),
            Optional()
        ],
        description="Upload a PDB file for the molecule"
    )
    
    contact_distance = FloatField(
        'Contact Distance (nm)',
        validators=[
            NumberRange(min=0.1, max=10.0, 
                       message="Contact distance must be between 0.1 and 10.0 nm"),
            DataRequired()
        ],
        default=1.5,
        description="Distance between molecules in the fibril"
    )
    
    fibril_length = FloatField(
        'Fibril Length (nm)',
        validators=[
            NumberRange(min=1.0, max=1000.0,
                       message="Fibril length must be between 1.0 and 1000.0 nm"),
            DataRequired()
        ],
        default=100.0,
        description="Length of the collagen fibril"
    )
    
    use_gromacs = BooleanField(
        'Generate GROMACS Files',
        default=False,
        description="Generate topology and configuration files for GROMACS"
    )
    
    gromacs_force_field = SelectField(
        'Force Field',
        choices=[
            ('charmm36', 'CHARMM36'),
            ('amber99sb-ildn', 'AMBER99SB-ILDN'),
            ('gromos54a7', 'GROMOS54a7')
        ],
        validators=[Optional()],
        description="Select force field for GROMACS simulation"
    )
    
    crosslink_density = FloatField(
        'Crosslink Density (%)',
        validators=[
            NumberRange(min=0.0, max=100.0,
                       message="Density must be between 0% and 100%"),
            Optional()
        ],
        default=30.0,
        description="Percentage of possible crosslink sites to fill"
    )
    
    def validate_existing_molecule_id(self, field):
        """Validate molecule selection."""
        if self.molecule_source.data == 'existing' and not field.data:
            raise ValidationError('Please select a molecule')
            
    def validate_molecule_file(self, field):
        """Validate molecule file upload."""
        if self.molecule_source.data == 'upload':
            if not field.data:
                raise ValidationError('Please upload a PDB file')