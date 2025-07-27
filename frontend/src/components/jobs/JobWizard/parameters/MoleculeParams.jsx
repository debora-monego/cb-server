import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../../../../utils/auth';

export default function MoleculeParams({ formData, onChange, onNext, onPrevious }) {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [availableSpecies, setAvailableSpecies] = useState([]);
  const [crosslinkData, setCrosslinkData] = useState(null);
  const [inputMethod, setInputMethod] = useState(formData.inputMethod || 'species');

  // Process crosslink data for the selected species
  const getSpeciesCrosslinkData = (species) => {
    if (!crosslinkData || !species) return null;

    const speciesData = crosslinkData.filter(item => item.species === species);
    const nTerminalData = speciesData.filter(item => item['RES-terminal'] === 'LYS-N');
    const cTerminalData = speciesData.filter(item => item['RES-terminal'] === 'LYS-C');

    const processTerminalData = (data) => {
      const types = [...new Set(data.map(item => item.type))];
      const positions = {};
      types.forEach(type => {
        positions[type] = [...new Set(data
          .filter(item => item.type === type)
          .map(item => item.position)
          .filter(pos => pos !== null)
        )];
      });
      
      return { types, positions };
    };

    return {
      n_terminal: processTerminalData(nTerminalData),
      c_terminal: processTerminalData(cTerminalData)
    };
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        console.log('Making request to /api/jobs/crosslinks-data...');
        const response = await fetchWithAuth('/api/jobs/crosslinks-data');
        
        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();
        if (data.status === 'success') {
          setAvailableSpecies(data.species || []);
          setCrosslinkData(data.crosslinks || null);
          console.log('Loaded data:', data);
        } else {
          throw new Error(data.message || 'Failed to load data');
        }
      } catch (err) {
        console.error('Error loading data:', err);
        setError(`Failed to load required data: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  const handleInputMethodChange = (value) => {
    setInputMethod(value);
    onChange({
      ...formData,
      inputMethod: value,
      enableCrosslinks: false,
      nTerminalType: 'NONE',
      cTerminalType: 'NONE',
      nTerminalPosition: null,
      cTerminalPosition: null,
      species: value === 'custom' ? null : formData.species,
      chainA: value === 'species' ? null : formData.chainA,
      chainB: value === 'species' ? null : formData.chainB,
      chainC: value === 'species' ? null : formData.chainC,
    });
  };

  const validateSequence = (sequence) => {
    if (!sequence) return false;
    if (sequence.length < 950 || sequence.length > 1150) return false;
    return /^[ABCDEFGHIKLMNOPQRSTUVWXYZ-]+$/.test(sequence);
  };

  const handleSubmit = () => {
    if (inputMethod === 'species') {
      if (!formData.species) {
        setError('Please select a species');
        return;
      }
    } else {
      // Validate custom sequences
      const sequences = ['chainA', 'chainB', 'chainC'];
      for (const chain of sequences) {
        if (!validateSequence(formData[chain])) {
          setError(`Invalid sequence for ${chain}. Length must be between 950-1150 and contain only valid amino acids.`);
          return;
        }
      }
    }

    // If crosslinks are enabled, validate crosslink selections
    if (formData.enableCrosslinks) {
      if (formData.nTerminalType !== 'NONE' && !formData.nTerminalPosition) {
        setError('Please select N-terminal position');
        return;
      }
      if (formData.cTerminalType !== 'NONE' && !formData.cTerminalPosition) {
        setError('Please select C-terminal position');
        return;
      }
    }

    setError(null);
    onNext();
  };

  const handleCrosslinkChange = (terminal, type, position = null) => {
    let updates = {
      ...formData,
      [`${terminal}TerminalType`]: type
    };
    
    if (position !== undefined) {
      updates[`${terminal}TerminalPosition`] = position;
    } else if (type === 'NONE') {
      updates[`${terminal}TerminalPosition`] = null;
    }
    
    onChange(updates);
  };

  const renderCrosslinkOptions = () => {
    if (!formData.enableCrosslinks || !formData.species) return null;

    const speciesData = getSpeciesCrosslinkData(formData.species);
    if (!speciesData) return null;

    return (
      <div className="space-y-4">
        {/* N-Terminal Options */}
        <div className="space-y-2">
          <label className="block text-sm font-medium">N-Terminal Type</label>
          <select
            value={formData.nTerminalType || 'NONE'}
            onChange={(e) => handleCrosslinkChange('n', e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="NONE">None</option>
            {speciesData.n_terminal.types.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          
          {formData.nTerminalType && formData.nTerminalType !== 'NONE' && (
            <div className="mt-2">
              <label className="block text-sm font-medium">N-Terminal Position</label>
              <select
                value={formData.nTerminalPosition || ''}
                onChange={(e) => handleCrosslinkChange('n', formData.nTerminalType, e.target.value)}
                className="w-full p-2 border rounded mt-1"
              >
                <option value="">Select position...</option>
                {speciesData.n_terminal.positions[formData.nTerminalType]?.map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* C-Terminal Options */}
        <div className="space-y-2">
          <label className="block text-sm font-medium">C-Terminal Type</label>
          <select
            value={formData.cTerminalType || 'NONE'}
            onChange={(e) => handleCrosslinkChange('c', e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="NONE">None</option>
            {speciesData.c_terminal.types.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          
          {formData.cTerminalType && formData.cTerminalType !== 'NONE' && (
            <div className="mt-2">
              <label className="block text-sm font-medium">C-Terminal Position</label>
              <select
                value={formData.cTerminalPosition || ''}
                onChange={(e) => handleCrosslinkChange('c', formData.cTerminalType, e.target.value)}
                className="w-full p-2 border rounded mt-1"
              >
                <option value="">Select position...</option>
                {speciesData.c_terminal.positions[formData.cTerminalType]?.map(pos => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Input Method Selection */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Sequence Input</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="species"
              value="species"
              checked={inputMethod === 'species'}
              onChange={(e) => handleInputMethodChange(e.target.value)}
              className="h-4 w-4 text-blue-600"
            />
            <label htmlFor="species" className="text-sm">Use Species Template</label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="custom"
              value="custom"
              checked={inputMethod === 'custom'}
              onChange={(e) => handleInputMethodChange(e.target.value)}
              className="h-4 w-4 text-blue-600"
            />
            <label htmlFor="custom" className="text-sm">Input Custom Sequences</label>
          </div>
        </div>

        {/* Species Selection or Custom Sequences */}
        {inputMethod === 'species' ? (
          <div className="space-y-4">
            <label className="block text-sm font-medium">Select Species</label>
            <select
              value={formData.species || ''}
              onChange={(e) => onChange({ ...formData, species: e.target.value })}
              className="w-full p-2 border rounded"
            >
              <option value="">Choose a species...</option>
              {availableSpecies.map(species => (
                <option key={species} value={species}>
                  {species.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div className="space-y-4">
            {['chainA', 'chainB', 'chainC'].map(chain => (
              <div key={chain}>
                <label className="block text-sm font-medium">{`Chain ${chain.slice(-1)}`}</label>
                <textarea
                  value={formData[chain] || ''}
                  onChange={(e) => onChange({
                    ...formData,
                    [chain]: e.target.value.toUpperCase()
                  })}
                  placeholder={`Enter sequence for chain ${chain.slice(-1)}...`}
                  rows={3}
                  className="w-full p-2 border rounded"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Length: {formData[chain]?.length || 0}/950-1150
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Crosslinks Configuration */}
      <div className="border rounded-lg p-6 space-y-4">
        <div>
          <h3 className="text-lg font-medium">Crosslinks Configuration</h3>
          <p className="text-sm text-gray-500">Configure N and C terminal crosslinks</p>
        </div>

        {inputMethod === 'species' ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <label htmlFor="enable-crosslinks" className="text-sm font-medium">Enable Crosslinks</label>
              <input
                type="checkbox"
                id="enable-crosslinks"
                checked={formData.enableCrosslinks || false}
                onChange={(e) => onChange({
                  ...formData,
                  enableCrosslinks: e.target.checked,
                  nTerminalType: 'NONE',
                  cTerminalType: 'NONE',
                  nTerminalPosition: null,
                  cTerminalPosition: null
                })}
                disabled={!formData.species}
                className="h-4 w-4 text-blue-600"
              />
            </div>
            {renderCrosslinkOptions()}
          </>
        ) : (
          <div className="bg-blue-50 border-blue-200 p-4 rounded">
            <p className="text-sm">
              Crosslink configuration is only available when using species templates. 
              Custom sequences require manual verification before crosslink application.
            </p>
          </div>
        )}
      </div>

      <div className="flex justify-between pt-6">
        <button
          type="button"
          onClick={onPrevious}
          className="px-4 py-2 border rounded hover:bg-gray-100"
        >
          Previous
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Next
        </button>
      </div>
    </div>
  );
}