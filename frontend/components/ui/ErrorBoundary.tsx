// components/ErrorBoundary.tsx
'use client'

import React from 'react'

type Props = {
  children: React.ReactNode
}

type State = {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Erreur capturée dans ErrorBoundary :', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 border border-red-500 rounded bg-red-50 text-red-800">
          <h2 className="font-bold text-lg mb-2">Une erreur est survenue</h2>
          <p>{this.state.error?.message || 'Erreur inconnue.'}</p>
        </div>
      )
    }

    return this.props.children
  }
}
