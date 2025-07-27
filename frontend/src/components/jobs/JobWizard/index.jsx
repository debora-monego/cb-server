import React, { useState } from 'react'
import { Progress } from '@/components/ui/progress'
import StepJobType from './StepJobType.jsx'
import StepBasicInfo from './StepBasicInfo.jsx'
import StepParameters from './StepParameters.jsx'
import StepReview from './StepReview.jsx'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn } from '@/lib/utils'

const STEPS = ['Select Type', 'Basic Info', 'Parameters', 'Review']

export default function JobWizard() {
  const [currentStep, setCurrentStep] = useState(0)
  const [jobType, setJobType] = useState(null)
  const [formData, setFormData] = useState({
    jobName: '',
    description: '',
    parameters: {}
  })
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const progress = ((currentStep) / (STEPS.length - 1)) * 100

  const handleNext = () => {
    setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1))
  }

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0))
  }

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true)
      setError(null)

      const response = await fetch('/jobs/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_type: jobType,
          ...formData,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || 'Failed to submit job')
      }

      // Redirect to job status page
      window.location.href = `/jobs/status/${data.job_id}`
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <StepJobType 
          selectedType={jobType} 
          onSelect={setJobType} 
          onNext={handleNext} 
        />
      case 1:
        return <StepBasicInfo 
          formData={formData} 
          onChange={setFormData} 
          onNext={handleNext}
          onPrevious={handlePrevious}
        />
      case 2:
        return <StepParameters
          jobType={jobType}
          formData={formData}
          onChange={setFormData}
          onNext={handleNext}
          onPrevious={handlePrevious}
        />
      case 3:
        return <StepReview
          jobType={jobType}
          formData={formData}
          onSubmit={handleSubmit}
          onPrevious={handlePrevious}
          isSubmitting={isSubmitting}
        />
      default:
        return null
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">Submit Job</h1>
        <div className="mb-4">
          <Progress value={progress} className="h-2" />
        </div>
        <div className="flex justify-between text-sm text-gray-600">
          {STEPS.map((step, index) => (
            <div
              key={step}
              className={cn(
                currentStep === index ? "font-medium text-primary" : 
                currentStep > index ? "text-gray-600" : "text-gray-400"
              )}
            >
              {step}
            </div>
          ))}
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {renderStep()}
    </div>
  )
}