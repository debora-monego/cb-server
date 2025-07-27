import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'

export default function StepBasicInfo({ formData, onChange, onNext, onPrevious }) {
  const handleChange = (field) => (e) => {
    onChange({ ...formData, [field]: e.target.value })
  }

  return (
    <Card>
      <CardContent className="space-y-4 pt-6">
        <div className="space-y-2">
          <label className="text-sm font-medium">Job Name</label>
          <Input
            value={formData.jobName || ''}
            onChange={handleChange('jobName')}
            placeholder="Enter a name for your job"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Description</label>
          <Textarea
            value={formData.description || ''}
            onChange={handleChange('description')}
            placeholder="Describe your job (optional)"
            rows={4}
          />
        </div>

        <div className="flex justify-between pt-4">
          <Button variant="outline" onClick={onPrevious}>
            Previous
          </Button>
          <Button onClick={onNext} disabled={!formData.jobName}>
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}