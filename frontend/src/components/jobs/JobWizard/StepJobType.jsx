import React from 'react'
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent 
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { 
  Dna,  // For molecular structure
  Box,  // For fibril structure
  Combine, // For mixed crosslinks
  ArrowDownAZ, // For reduced density
} from 'lucide-react'

const JOB_TYPES = {
  molecule: {
    title: 'Collagen Triple Helix',
    description: 'Create a new collagen molecule from scratch',
    icon: Dna,
    features: [
      'Choose from species templates or input custom sequences',
      'Validate amino acid composition and length',
      'Configure terminal crosslinks (optional)',
      'Generate PDB structure file'
    ],
    color: 'bg-blue-50 hover:bg-blue-100',
    iconColor: 'text-blue-600',
    note: 'Start here if you need a new molecule'
  },
  standardFibril: {
    title: 'Standard Fibril',
    description: 'Build a fibril from an existing molecule',
    icon: Box,
    features: [
      'Use existing molecule PDB file',
      'Define fibril dimensions',
      'Optional GROMACS topology',
      'Standard crosslink configuration'
    ],
    color: 'bg-green-50 hover:bg-green-100',
    iconColor: 'text-green-600',
    note: 'Basic fibril assembly with regular structure'
  },
  mixedFibril: {
    title: 'Mixed-Crosslink Fibril',
    description: 'Create fibril combining different crosslink types',
    icon: Combine,
    features: [
      'Combine multiple crosslink configurations',
      'Upload reference PDB structures',
      'Specify mixture ratios',
      'Generate composite topology'
    ],
    color: 'bg-purple-50 hover:bg-purple-100',
    iconColor: 'text-purple-600',
    note: 'Advanced: requires multiple reference structures'
  },
  reducedFibril: {
    title: 'Reduced-Density Fibril',
    description: 'Create fibril with lower crosslink density',
    icon: ArrowDownAZ,
    features: [
      'Specify density reduction percentage',
      'Based on standard fibril structure',
      'Maintain structural integrity',
      'Controlled crosslink removal'
    ],
    color: 'bg-amber-50 hover:bg-amber-100',
    iconColor: 'text-amber-600',
    note: 'Modification of standard fibril structure'
  }
}

export default function StepJobType({ selectedType, onSelect, onNext }) {
  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Select Job Type</h2>
        <p className="text-sm text-gray-600">Choose the type of structure you want to create</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(JOB_TYPES).map(([type, info]) => {
          const Icon = info.icon
          return (
            <Card 
              key={type}
              className={cn(
                "cursor-pointer transition-all border-2",
                info.color,
                selectedType === type 
                  ? "ring-2 ring-primary border-primary transform scale-[1.02]" 
                  : "hover:shadow-lg border-transparent hover:scale-[1.01]"
              )}
              onClick={() => onSelect(type)}
            >
              <CardHeader>
                <div className="flex items-start space-x-4">
                  <div className={cn(
                    "p-3 rounded-xl", 
                    info.color,
                    info.iconColor
                  )}>
                    <Icon size={28} />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{info.title}</CardTitle>
                    <CardDescription className="mt-1">{info.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 mb-4">
                  {info.features.map((feature, index) => (
                    <li key={index} className="flex items-start text-sm text-gray-600">
                      <span className="mr-2 mt-1 text-xs">•</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <div className="text-xs text-gray-500 italic">
                  {info.note}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="flex justify-between pt-4 border-t">
        <div className="text-sm text-gray-600">
          {selectedType ? `Selected: ${JOB_TYPES[selectedType].title}` : 'Please select a job type to continue'}
        </div>
        <Button
          onClick={onNext}
          disabled={!selectedType}
          className="px-6"
        >
          Continue
        </Button>
      </div>
    </div>
  )
}