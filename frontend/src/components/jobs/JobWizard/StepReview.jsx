import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function StepReview({ jobType, formData, onSubmit, onPrevious, isSubmitting }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Review Job Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div>
            <span className="font-medium">Job Type:</span> {jobType}
          </div>
          <div>
            <span className="font-medium">Name:</span> {formData.jobName}
          </div>
          {formData.description && (
            <div>
              <span className="font-medium">Description:</span> {formData.description}
            </div>
          )}
        </div>

        <div className="flex justify-between pt-4">
          <Button variant="outline" onClick={onPrevious}>
            Previous
          </Button>
          <Button 
            onClick={onSubmit} 
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Job'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}