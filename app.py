from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from wtforms import StringField, PasswordField, SelectField, SubmitField, BooleanField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import subprocess
import os
from pathlib import Path
import pandas as pd
import yaml
import requests
from celery_config import make_celery
from dataclasses import dataclass, asdict

import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/download/app.log'),
        logging.StreamHandler()
    ]
)

# TODO: implement flask.migrate to introduce changes to the existing DB

# Environment specific variables
app = Flask(__name__)
disallowed_countries = os.getenv('DISALLOWED_COUNTRIES', 'IR,RU') # Default value for debugging, should be set in ~/.bashrc
DISALLOWED_COUNTRIES = set(disallowed_countries.split(','))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key') # should be set in ~/.bashrc to make it env specific
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'  # Replace with your broker URL
# app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config.update(
    result_backend='redis://localhost:6379/0',
    broker_url='redis://localhost:6379/0'
)
# logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='a',
#                     format='%(name)s - %(levelname)s - %(message)s')
celery = make_celery(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    '''
    Entries in the database for the registered users
    '''
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    jobs = db.relationship('Job', backref='user', lazy=True)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


class Job(db.Model):
    '''
    Entries in the database for the user jobs
    '''
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    result_path = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organism = db.Column(db.String(50))
    n_terminal_crosslink = db.Column(db.String(50))
    c_terminal_crosslink = db.Column(db.String(50))
    n_terminal_position = db.Column(db.String(50))
    c_terminal_position = db.Column(db.String(50))
    celery_task_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='PENDING')
    output = db.Column(db.Text)
    error_message = db.Column(db.Text)


class CrosslinkingData():
    '''
    Class to handle the selection of crosslinking data by user
    '''
    def __init__(self):
        crosslinks_data_dir = os.path.join(app.root_path, '/opt/server/static', 'crosslinks')
        self.data = pd.read_csv(os.path.join(crosslinks_data_dir, 'transformed_crosslink_data_all_combinations.csv'))

    def get_species(self):
        species = self.data['species'].unique()
        species_list = [(str(s), str(s)) for s in species]
        species_list.insert(0, ('custom', 'Custom sequence'))
        return species_list
        
    def get_crosslink_types(self):
        xl_types = self.data['type'].unique()
        crosslink_types = [('', 'Select crosslink type')] + [(str(xl), str(xl)) for xl in xl_types if xl]
        return crosslink_types

    def get_positions_for_type(self, species, crosslink_type, terminus: str):
        '''
        Find positions specific for the species, selected crosslink type and the selected N or C terminus
        Arguments:
            species(str): user-selected species in the form
            crosslink_type(str): user-selected crosslink type in the form
            terminus(str): N or C-termins selected by the user in the form
        '''
        filtered_data = self.data[(self.data['species'] == species) &
                                  (self.data['type'] == crosslink_type)]
        if terminus == 'N':
            positions = filtered_data[filtered_data['RES-terminal'].str.endswith('N')]['combination'].unique()
        elif terminus == 'C':
            positions = filtered_data[filtered_data['RES-terminal'].str.endswith('C')]['combination'].unique()
        else:
            positions = []
        return positions.tolist()
    
@dataclass
class FormData:
    description: str
    organism: str
    n_terminal_crosslink: str
    c_terminal_crosslink: str
    n_terminal_position: str
    c_terminal_position: str
    generate_sequence: bool
    generate_geometry: bool
    generate_topology: bool
    crosslink: bool
    contact_distance: float
    fibril_length: float
    mix_bool: bool
    ratio_mix: str
    replace_bool: bool
    ratio_replace: float
    crystalcontacts_optimize: bool
    force_field: str
    fasta_file: str = None 
    file_a_path: str = None
    file_b_path: str = None
    
@app.route('/get-positions')
def get_positions():
    '''
    Fetch positions for the selected species, crosslink type and terminus
    '''
    species = request.args.get('species')
    crosslink_type = request.args.get('type')
    terminus = request.args.get('terminus') 
    positions = CrosslinkingData().get_positions_for_type(species, crosslink_type, terminus)
    # For debugging:
    logging.debug(f"Positions for species: {species}, type: {crosslink_type}, terminus: {terminus} -> {positions}")
    return jsonify({'positions': positions})


class JobSubmissionForm(FlaskForm):
    '''
    Class to handle the form for job submission form with all input fields
    '''
    # Homology modeling data
    CROSSLINKING_DATA = CrosslinkingData()
    description = StringField('Description', validators=[DataRequired()])
    generate_sequence = BooleanField('Generate Collagen Molecule', default=True)
    organism = SelectField('Organism', choices=CROSSLINKING_DATA.get_species(), validators=[])
    crosslink = BooleanField('Enable Crosslinking', default=False)
    n_terminal_crosslink = SelectField('N-terminal crosslink type', choices=CROSSLINKING_DATA.get_crosslink_types(), validators=[])
    c_terminal_crosslink = SelectField('C-terminal crosslink type', choices=CROSSLINKING_DATA.get_crosslink_types(), validators=[])
    n_terminal_position = SelectField('N-terminal Position', choices=[], validators=[])
    c_terminal_position = SelectField('C-terminal Position', choices=[], validators=[])
    fasta_sequences = TextAreaField('Enter FASTA Sequences', validators=[DataRequired()], 
                                    render_kw={"rows": 10, "cols": 40},
                                    default=">MyCustomSpecies:chainA\nQLSYGYDEKSTGGISVPGPMGPSGPRGLOGP...\n>MyCustomSpecies:chainB\nQYDGKGVGLGPGPMGLMGPRGPOGAAG...\n>MyCustomSpecies:chainC\nQLSYGYDEKSTGGISVPGPMGPSGPRGLOGP...")
    pdb_file = FileField('Upload PDB File', validators=[FileAllowed(['pdb'], 'PDB files only!')])

    # Geometry generation data
    generate_geometry = BooleanField('Generate Collagen Fibril', default=True)
    contact_distance = FloatField('Contact Distance (Å)',
                                  validators=[],
                                  description="Required when generating geometry")
    
    fibril_length = FloatField('Fibril Length (nm)',
                               validators=[],
                               description="Required when generating geometry")
    crystalcontacts_optimize = BooleanField('Optimize Crystal Contacts', default=False)  # Add this field
    mix_bool = BooleanField('Enable Mixing', default=False)
    file_a = FileField('PDB File for Crosslink A',
                       validators=[FileAllowed(['pdb'], 'PDB files only!')])
    file_b = FileField('PDB File for Crosslink B',
                       validators=[FileAllowed(['pdb'], 'PDB files only!')])
    type_a = SelectField('Type of Crosslink A',
                         choices=[('NONE', 'NONE'), ('D', 'D'), ('T', 'T'), ('DT', 'DT')],
                         default='NONE')
    type_b = SelectField('Type of Crosslink B',
                         choices=[('NONE', 'NONE'), ('D', 'D'), ('T', 'T'), ('DT', 'DT')],
                         default='NONE')
    replace_bool = BooleanField('Enable Replacement', default=False)
    ratio_replace = FloatField('Replacement Ratio', validators=[Optional()])
    generate_topology = BooleanField('Generate Topology', default=False)
    force_field = SelectField('Force Field Selection', 
                            choices=[('amber99', 'AMBER99SB-ILDN'), ('martini3', 'Martini 3')],
                            default='amber99',
                            validators=[])
    submit = SubmitField('Submit Job')

    def __init__(self, *args, **kwargs):
        super(JobSubmissionForm, self).__init__(*args, **kwargs)
        # Set default organism to "custom" if "Generate Collagen Molecule" is unchecked
        self.organism.choices = self.CROSSLINKING_DATA.get_species()
        
        # Ensure 'custom' is a valid choice
        if ('custom', 'Custom sequence') not in self.organism.choices:
            self.organism.choices.append(('custom', 'Custom sequence'))
        
        # Set default organism to "custom" if "Generate Collagen Molecule" is unchecked
        if not self.generate_sequence.data:
            self.organism.default = "custom"
            self.organism.data = "custom"

    def validate(self, **kwargs):
        '''
        Validation logic to conditionally require fields based on the crosslink selection according to the colbuilder requirements
        '''
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        # If Generate Sequence is selected, organism must not be "custom"
        if self.generate_sequence.data:
            # If generating sequence and using custom organism, ensure FASTA is provided
            if self.organism.data == "custom":
                if not self.fasta_sequences.data:
                    self.fasta_sequences.errors.append('FASTA sequences are required for custom sequence.')
                    return False
            elif not self.organism.data or self.organism.data == 'None':
                self.organism.errors.append('Please select a valid organism.')
                return False
        else:
            # If not generating sequence, ensure PDB file is provided
            if self.generate_geometry.data and not self.pdb_file.data:
                self.pdb_file.errors.append('PDB file is required when not generating sequence.')
                return False
        
        # If generate_geometry is selected, make contact_distance and fibril_length required
        if self.generate_geometry.data:
            if not self.contact_distance.data:
                self.contact_distance.errors.append('Contact distance is required when generating collagen fibril.')
                return False
            if not self.fibril_length.data:
                self.fibril_length.errors.append('Fibril length is required when generating collagen fibril.')
                return False
        else:
            # If generate_geometry is not selected, remove the DataRequired validator
            self.contact_distance.validators = []
            self.fibril_length.validators = []
            
        if self.generate_topology.data:
            if not self.force_field.data:
                self.force_field.errors.append('Force Field Selection is required when generating topology.')
                return False
            if self.force_field.data == 'martini3':
                self.force_field.errors.append('Martini 3 force field is not yet available.')
                return False

        if self.crosslink.data:  # Only validate crosslink fields if crosslinking is enabled
            if not self.n_terminal_crosslink.data or not self.c_terminal_crosslink.data:
                self.crosslink.errors.append('Please select both N-terminal and C-terminal crosslink types.')
                return False
            if not self.n_terminal_position.data or not self.c_terminal_position.data:
                self.crosslink.errors.append('Please select both N-terminal and C-terminal positions.')
                return False
        
        if self.mix_bool.data:  # Only validate mix-related fields if mix_bool is checked
            if not self.file_a.data:
                self.file_a.errors.append("Please provide a PDB file for Crosslink A.")
                return False
            if not self.file_b.data:
                self.file_b.errors.append("Please provide a PDB file for Crosslink B.")
                return False
            if self.type_a.data == "NONE":
                self.type_a.errors.append("Please select a valid type for Crosslink A.")
                return False
            if self.type_b.data == "NONE":
                self.type_b.errors.append("Please select a valid type for Crosslink B.")
                return False
        
        return True


class RegistrationForm(FlaskForm):
    '''
    Class to handle the form for user registration with all input fields
    '''
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')


class HomeForm(FlaskForm):
    '''
    empty for now; some functionality needed?
    # TODO: clarify what home should contain and what not
    '''


class LoginForm(FlaskForm):
    '''
    Class to handle the form for user login with all input fields
    '''
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


'''
App routing begins here:
'''

@app.route('/', methods=['GET', 'POST'])
def blank():
    return redirect(url_for('home'))


@app.route('/home', methods=['GET', 'POST'])
def home():
    form = HomeForm()
    return render_template('home.html', form=form)


@app.route('/help')
def help():
    return render_template('help.html')


def get_country_from_ip(ip_address):
    # TODO: benchmark and modify, I suspect the solution is quite raw
    '''
    Fetches the country code from the IP address using an IP Geolocation API
    '''
    url = f'https://ipinfo.io/{ip_address}/json?'  # For ipinfo.io, modify URL if using a different service
    try:
        response = requests.get(url)
        data = response.json()
        country = data.get('country')  # Get country code from the API response
        logging.debug(f'Country code for IP {ip_address}: {country}')
        return country
    except Exception as e:
        logging.debug(f'Error getting country from IP: {e}')
        return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
    Fetches user's IP address and checks if the country is in the disallowed list
    If the country is disallowed, the user is informed and the registration cannot conclude
    Otherwise, the registration is handled and the user's credentials are stored in the database
    '''
    if False:
        # Fetch user's IP address (handling proxies)
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        try:
            response = requests.get(f'https://ipapi.co/{user_ip}/json/')
            data = response.json()
            country_code = data.get('country')
            country_name = data.get('country_name')
            if country_code in DISALLOWED_COUNTRIES:
                flash(f'Unfortunately, registration is not allowed from your location: {country_name} (IP: {user_ip}).', 'danger')
                return render_template('register.html', show_form=False)
        except Exception as e:
            app.logger.error(f'Error checking location for IP {user_ip}: {e}')
            flash(f'Error checking your location. Please try again later.', 'danger')
            return render_template('register.html', show_form=False)

    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email is already registered
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Proceed to login or select another email.', 'error')
            return render_template('register.html', form=form, show_form=True)
        # Check if username is already taken
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'error')
            return render_template('register.html', form=form, show_form=True)

        # Hash password and create new user
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, show_form=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Login page for the user to enter their credentials
    '''
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password.data):
               login_user(user)
               flash('Login successful!', 'success')
               return redirect(url_for('home'))  # Redirect to the home page where the message should appear
            else:
               flash('Invalid username or password. Please try again.', 'danger')
        else:
            flash('Invalid username or password. Please try again.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    '''
    Logs out the user and redirects to the login page.
    '''
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@celery.task(bind=True)
def run_colbuilder_task(self, 
                        form_data: dict,
                        result_path: str,
                        job_id: str,
                        fasta_file_path: str = None,
                        pdb_file_path: str = None):
    """
    Creates a YAML configuration file based on form data and runs colbuilder using subprocess
    Args:
        - form_data: FormData object converted to a dict containing the form data
        - result_path: The path to store the results and YAML configuration files
        - job_id: The unique job identifier
        - fasta_file_path: The path to the uploaded FASTA file (if provided)
        - pdb_file_path: The path to the uploaded PDB file (if provided)
    Returns:
        - tar_path (str): The path to the generated tar file containing the results if the execution succeeds
    Raises:
        - subprocess.CalledProcessError: If the subprocess execution fails
    """
    logger = logging.getLogger('celery')
    try:
        # Initial logging of input data
        logger.debug(f"Starting task with form_data: {form_data}")
        logger.debug(f"Result path: {result_path}")
        logger.debug(f"Job ID: {job_id}")
        logger.debug(f"FASTA file path: {fasta_file_path}")
        logger.debug(f"PDB file path: {pdb_file_path}")
        logger.debug(f"Topology generator enabled: {form_data.get('generate_topology')}")
        logger.debug(f"Force field value received: {form_data.get('force_field')}")

        # Set the task state to 'STARTED'
        self.update_state(state='STARTED', meta={'status': 'Task started'})

        # Generate filenames and paths
        base_filename = f"{secure_filename(form_data['description'])}-{job_id}"
        yaml_filename = f"{base_filename}.yaml"
        yaml_full_path = os.path.join(result_path, yaml_filename)
        yaml_full_path_abs = os.path.abspath(yaml_full_path)
        logger.debug(f"YAML file will be written to: {yaml_full_path_abs}")
        
        # Create initial YAML config
        yaml_config = {
            'mode': None,
            'config_file': None,
            'sequence_generator': form_data['generate_sequence'],
            'geometry_generator': form_data['generate_geometry'],
            'topology_generator': form_data['generate_topology'],
            'debug': False,
            'working_directory': "./",
            'species': form_data['organism'],
            'fasta_file': fasta_file_path if fasta_file_path else None,
            'crosslink': form_data['crosslink']
        }
        logger.debug("Initial YAML config created: %s", yaml_config)
        
        # Handle force field explicitly
        if form_data['generate_topology']:
            logger.debug("Topology generation is enabled, checking force field...")
            force_field = form_data.get('force_field')
            logger.debug(f"Force field value to be added: {force_field}")
            yaml_config.update({'force_field': force_field})
            logger.debug(f"Added force field to config: {yaml_config.get('force_field')}")
            
        # Sequence Settings
        if form_data['crosslink']:
            logger.debug("Adding crosslink settings...")
            yaml_config.update({
                'n_term_type': form_data['n_terminal_crosslink'],
                'c_term_type': form_data['c_terminal_crosslink'],
                'n_term_combination': form_data['n_terminal_position'],
                'c_term_combination': form_data['c_terminal_position'],
            })
            logger.debug("After crosslink update: %s", yaml_config)

        # Geometry Settings
        if form_data['generate_geometry']:
            logger.debug("Adding geometry settings...")
            yaml_config.update({
                'pdb_file': pdb_file_path if pdb_file_path else None,
                'contact_distance': form_data['contact_distance'],
                'fibril_length': form_data['fibril_length'],
                'crystalcontacts_optimize': form_data['crystalcontacts_optimize']
            })
            logger.debug("After geometry update: %s", yaml_config)
        
        # Mixing Settings
        if form_data['mix_bool']:
            logger.debug("Adding mixing settings...")
            file_a_name = os.path.basename(form_data['file_a_path']) if form_data['file_a_path'] else None
            file_b_name = os.path.basename(form_data['file_b_path']) if form_data['file_b_path'] else None
            
            yaml_config.update({
                'mix_bool': True,
                'ratio_mix': form_data['ratio_mix'],
                'files_mix': [file_a_name, file_b_name]
            })
            logger.debug("After mix update: %s", yaml_config)
            
        # Replacement Settings
        if form_data['replace_bool']:
            logger.debug("Adding replacement settings...")
            yaml_config.update({
               'replace_bool': True,
               'ratio_replace': form_data['ratio_replace']
            })
            logger.debug("After replace update: %s", yaml_config)

        logger.debug("Final YAML config before writing: %s", yaml_config)
        
        # Write YAML file
        try:
            with open(yaml_full_path_abs, 'w') as yaml_file:
                yaml.dump(yaml_config, yaml_file, default_flow_style=False, sort_keys=False)
            logger.debug("Successfully wrote YAML file")
            
            # Verify the written content
            with open(yaml_full_path_abs, 'r') as yaml_file:
                written_config = yaml.safe_load(yaml_file)
                logger.debug("Verified written YAML content: %s", written_config)
        except Exception as yaml_error:
            logger.error(f"Error writing YAML file: {str(yaml_error)}")
            raise
    
        # Colbuilder execution
        script_name = '/opt/venv/bin/colbuilder'
        args = ['--config_file', yaml_full_path_abs]
        command = [script_name] + args

        logger.debug(f"Preparing to execute command: {' '.join(command)}")
        logger.debug(f"Working directory: {result_path}")

        try:
            # Run the command using subprocess
            result = subprocess.run(
                command,
                text=True,
                capture_output=True,
                cwd=result_path,
                env=os.environ,
                check=False  # Don't raise exception immediately
            )

            # Log command output
            logger.debug(f"Command stdout: {result.stdout}")
            logger.debug(f"Command stderr: {result.stderr}")
            logger.debug(f"Command return code: {result.returncode}")

            if result.returncode == 0:
                # Task is successful, create tar file
                tar_filename = f"{base_filename}.tar.gz"
                tar_path = os.path.join(result_path, tar_filename)

                logger.debug(f"Creating tar file at: {tar_path}")
                subprocess.run(
                    ['tar', '-czvf', os.path.join('/download', tar_filename), '.'],
                    check=True,
                    cwd=result_path
                )
                
                self.update_state(state='PROGRESS', 
                                meta={'status': 'Task in progress', 'step': 'Tar file created'})
                return str(os.path.join('/download', tar_filename))
            else:
                detailed_error = (
                    f"\nCommand failed with return code {result.returncode}"
                    f"\nCommand: {' '.join(command)}"
                    f"\nWorking directory: {result_path}"
                    f"\nStandard output: {result.stdout}"
                    f"\nStandard error: {result.stderr}"
                )
                logger.error(detailed_error)
                self.update_state(state='FAILURE', 
                                meta={'exc_type': 'SubprocessError', 
                                     'status': result.stderr or detailed_error})
                raise subprocess.CalledProcessError(
                    result.returncode, 
                    command, 
                    output=result.stdout, 
                    stderr=result.stderr
                )

        except subprocess.CalledProcessError as e:
            logger.error(f"Subprocess error: {str(e)}")
            raise

    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message, exc_info=True)
        self.update_state(state='FAILURE', 
                         meta={'exc_type': type(e).__name__, 'status': error_message})
        raise Exception(error_message)


@app.route('/submit-job', methods=['GET', 'POST'])
@login_required
def submit_job():
    '''
    Job submission form for the user to enter the job details

    '''
    form = JobSubmissionForm()

    if request.method == 'POST':
        if form.crosslink.data:
            # Update choices for N-terminal and C-terminal positions based on user selections
            selected_organism = form.organism.data
            selected_n_type = form.n_terminal_crosslink.data
            selected_c_type = form.c_terminal_crosslink.data

            logging.debug(f"Selected organism: {selected_organism}")
            logging.debug(f"Selected N-terminal crosslink type: {selected_n_type}")
            logging.debug(f"Selected C-terminal crosslink type: {selected_c_type}")

            # Dynamically update choices for n_position and c_position
            form.n_terminal_position.choices = [(pos, pos) for pos in CrosslinkingData().get_positions_for_type(
                species=selected_organism, crosslink_type=selected_n_type, terminus='N')]
            form.c_terminal_position.choices = [(pos, pos) for pos in CrosslinkingData().get_positions_for_type(
                species=selected_organism, crosslink_type=selected_c_type, terminus='C')]

            # Preserve the selected values
            form.n_terminal_position.data = request.form.get('n_terminal_position')
            form.c_terminal_position.data = request.form.get('c_terminal_position')

            logging.debug(f"Selected N-terminal position: {form.n_terminal_position.data}")
            logging.debug(f"Selected C-terminal position: {form.c_terminal_position.data}")

        else:
            # Set choices to None when crosslinking is not enabled
            form.n_terminal_crosslink.choices = [("", "None")]
            form.c_terminal_crosslink.choices = [("", "None")]
            form.n_terminal_position.choices = [("", "None")]
            form.c_terminal_position.choices = [("", "None")]

            # Set data to empty strings to avoid validation errors
            form.n_terminal_crosslink.data = ""
            form.c_terminal_crosslink.data = ""
            form.n_terminal_position.data = ""
            form.c_terminal_position.data = ""

    if form.validate_on_submit():
        job_id = int(datetime.utcnow().timestamp())
        result_path = f'jobs_results/{job_id}'
        os.makedirs(os.path.join('/opt/server/static', result_path), exist_ok=True)

        fasta_file_path = None
        if form.generate_sequence.data and form.organism.data == "custom":  # Changed from "Custom species" to "custom"
            if form.fasta_sequences.data:
                fasta_content = form.fasta_sequences.data
                fasta_file_path = os.path.join('/opt/server/static', result_path, 'user_fasta.fasta')
                fasta_file_path = os.path.abspath(fasta_file_path)
                
                # Write the content to the file
                with open(fasta_file_path, 'w') as fasta_file:
                    fasta_file.write(fasta_content)
                
                logging.debug(f"Saved FASTA file at: {fasta_file_path}")
            else:
                flash('FASTA sequences are required for custom species.', 'error')
                return render_template('submit_job.html', form=form)

        # Handle file upload if a PDB file is provided
        pdb_file_path = None
        if form.pdb_file.data:
            pdb_file = form.pdb_file.data
            filename = secure_filename(pdb_file.filename)
            pdb_file_path = os.path.join('/opt/server/static', result_path, filename)
            pdb_file_path = os.path.abspath(pdb_file_path)
            pdb_file.save(pdb_file_path)

        file_a_path = None
        file_b_path = None
        if request.form.get('mix_bool'):
            # Get the percentage values from the form
            percent_a = request.form.get('percent_a', type=int)
            percent_b = request.form.get('percent_b', type=int)
            type_a = request.form.get('type_a')
            type_b = request.form.get('type_b')
            
            # Format the ratio string
            ratio_mix = f"{type_a}:{percent_a} {type_b}:{percent_b}"

            # Handle file uploads
            if 'file_a' in request.files and 'file_b' in request.files:
                file_a = request.files['file_a']
                file_b = request.files['file_b']
                
                if file_a and file_b:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.join('/opt/server/static', result_path), exist_ok=True)
                    
                    # Save files with absolute paths
                    file_a_path = os.path.join('/opt/server/static', result_path, secure_filename(file_a.filename))
                    file_b_path = os.path.join('/opt/server/static', result_path, secure_filename(file_b.filename))
                    file_a_path = os.path.abspath(file_a_path)
                    file_b_path = os.path.abspath(file_b_path)
                    
                    # Save the files
                    file_a.save(file_a_path)
                    file_b.save(file_b_path)

        pdb_filename = Path(pdb_file_path).name if pdb_file_path else None
        
        if request.form.get('replace_bool'):
            ratio_replace = request.form.get('ratio_replace')
            
        force_field = None
        if form.generate_topology.data:
            # Get force field value directly from request.form
            force_field = request.form.get('force_field')
            logging.debug(f"Force field selected: {force_field}")
        
        if request.form.get('generate_geometry'):
            contact_distance = request.form.get('contact_distance', default=60, type=float)
            fibril_length = request.form.get('fibril_length', default=334, type=float)
            crystalcontacts_optimize = request.form.get('crystalcontacts_optimize', default=False, type=bool)
        else:
            contact_distance = None
            fibril_length = None
            crystalcontacts_optimize = False

        logging.debug(f"Form data: {form.data}")
        logging.debug(f"FASTA file path: {fasta_file_path}")

        # FormData class for the form data to pass to the Celery task less error-prone
        form_data = FormData(
                description=form.description.data,
                organism=form.organism.data,
                fasta_file=fasta_file_path,
                n_terminal_crosslink=form.n_terminal_crosslink.data,
                c_terminal_crosslink=form.c_terminal_crosslink.data,
                n_terminal_position=form.n_terminal_position.data,
                c_terminal_position=form.c_terminal_position.data,
                generate_sequence=form.generate_sequence.data,
                generate_geometry=form.generate_geometry.data,
                generate_topology=form.generate_topology.data,
                crosslink=form.crosslink.data,
                contact_distance=contact_distance,
                fibril_length=fibril_length,
                mix_bool=bool(request.form.get('mix_bool')),
                ratio_mix=ratio_mix if request.form.get('mix_bool') else None,
                file_a_path=file_a_path,
                file_b_path=file_b_path,
                replace_bool=bool(request.form.get('replace_bool')),
                ratio_replace=ratio_replace if request.form.get('replace_bool') else None,
                crystalcontacts_optimize=crystalcontacts_optimize,
                force_field=force_field
            )

        # Start the Celery task
        task = run_colbuilder_task.apply_async(args=[asdict(form_data), os.path.join('/opt/server/static', result_path), job_id, fasta_file_path, pdb_file_path])

       # Save job information in the database
        new_job = Job(
            description=form.description.data,
            organism=form.organism.data,
            n_terminal_crosslink=form.n_terminal_crosslink.data,
            c_terminal_crosslink=form.c_terminal_crosslink.data,
            n_terminal_position=form.n_terminal_position.data,
            c_terminal_position=form.c_terminal_position.data,
            user_id=current_user.id,
            output="Job is being processed.",
            result_path=None,  # No result path yet; will be updated after the task completes
            status='PENDING',
            celery_task_id=task.id
        )
        db.session.add(new_job)
        db.session.commit()

        flash('Job successfully submitted and is running!', 'success')
        return redirect(url_for('submit_job'))
    
    else:
        # Form validation failed
        logging.debug("Form validation failed.")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
    return render_template('submit_job.html', form=form)


@app.route('/job-status/<task_id>')
@login_required
def job_status(task_id):
    '''
    Dynamic job status update based on the status of the Celery task
    '''
    # Fetch the job from the database for the current user
    job = Job.query.filter_by(celery_task_id=task_id, user_id=current_user.id).first()
    if job.status in ['SUCCESS', 'FAILURE']:
        if job.status == 'SUCCESS':
            response = {
                'state': job.status,
                'status': 'Job completed',
                'download_url': url_for('download_results', filename=os.path.basename(job.result_path))
            }
        else:
            response = {
                'state': job.status,
                'status': 'Job failed'
            }
        return jsonify(response)

    # Otherwise, check the Celery task status
    task = run_colbuilder_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state, 
            'status': 'Pending...'}
    elif task.state == 'SUCCESS':
        if task.result and isinstance(task.result, str):
            job.result_path = task.result
        else:
            job.result_path = 'Unknown'
        # Update the job status in the database
        job.status = 'SUCCESS'
        db.session.commit()
        response = {
            'state': task.state,
            'status': 'Job completed',
            'download_url': url_for('download_results', filename=os.path.basename(job.result_path))
        }
    elif task.state == 'FAILURE':
        job.status = 'FAILURE'
        db.session.commit()
        response = {
            'state': task.state,
            'status': str(task.info)  # The exception raised
        }
    else:
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
        }
    return jsonify(response)


@app.route('/jobs')
@login_required
def view_jobs():
    jobs = Job.query.filter_by(user_id=current_user.id).all()
    return render_template('jobs.html', jobs=jobs)

@app.route('/download/<path:filename>', methods=['GET'])
@login_required
def download_results(filename):
    # Files are now stored in the static folder under jobs_results
    results_directory = '/download'
    if filename.startswith('/download/'):
        filename = filename[len('/download/'):]

    if os.path.exists(os.path.join(results_directory, filename)):
        return send_from_directory(results_directory, filename, as_attachment=True)
    else:
        flash('The requested file is not available.', 'error')
        return redirect(url_for('submit_job'))


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)

