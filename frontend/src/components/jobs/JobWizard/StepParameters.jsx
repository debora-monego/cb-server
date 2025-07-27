import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import MoleculeParams from './parameters/MoleculeParams'
import StandardFibrilParams from './parameters/StandardFibrilParams'
import MixedFibrilParams from './parameters/MixedFibrilParams'
import ReducedFibrilParams from './parameters/ReducedFibrilParams'
import { Button } from '@/components/ui/button'

export default function StepParameters({ 
  jobType, 
  formData, 
  onChange, 
  onNext, 
  onPrevious 
}) {
  const renderParameters = () => {
    const commonProps = { 
      formData: formData.parameters || {}, 
      onChange: (params) => onChange({ ...formData, parameters: params }),
      onNext,
      onPrevious
    }

    switch (jobType) {
      case 'molecule':
        return <MoleculeParams {...commonProps} />
      case 'standardFibril':
        return <StandardFibrilParams {...commonProps} />
      case 'mixedFibril':
        return <MixedFibrilParams {...commonProps} />
      case 'reducedFibril':
        return <ReducedFibrilParams {...commonProps} />
      default:
        return <div>Invalid job type</div>
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        {renderParameters()}
      </CardContent>
    </Card>
  )
}