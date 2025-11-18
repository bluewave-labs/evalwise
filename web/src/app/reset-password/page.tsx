"use client"

import { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Eye, EyeOff, CheckCircle, XCircle } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function ResetPasswordContent() {
    const searchParams = useSearchParams()
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)
    const [error, setError] = useState('')
    const [validationErrors, setValidationErrors] = useState<string[]>([])

    const token = searchParams?.get('token')

    useEffect(() => {
        if (!token) {
            setError('Invalid reset link. Please request a new password reset.')
        }
    }, [token])

    const validatePassword = (pwd: string): string[] => {
        const errors: string[] = []
        if (pwd.length < 8) errors.push('At least 8 characters long')
        if (!/[A-Z]/.test(pwd)) errors.push('One uppercase letter')
        if (!/[a-z]/.test(pwd)) errors.push('One lowercase letter')
        if (!/\d/.test(pwd)) errors.push('One number')
        return errors
    }

    useEffect(() => {
        if (password) {
            setValidationErrors(validatePassword(password))
        } else {
            setValidationErrors([])
        }
    }, [password])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        if (!token) {
            setError('Invalid reset token')
            setLoading(false)
            return
        }

        if (!password || !confirmPassword) {
            setError('Please fill in all fields')
            setLoading(false)
            return
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match')
            setLoading(false)
            return
        }

        const passwordErrors = validatePassword(password)
        if (passwordErrors.length > 0) {
            setError('Password does not meet requirements')
            setLoading(false)
            return
        }

        try {
            const response = await fetch(`${API_BASE_URL}/auth/password-reset/confirm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    token, 
                    new_password: password 
                }),
            })

            const data = await response.json()

            if (response.ok) {
                setSuccess(true)
            } else {
                if (data.detail?.details) {
                    // Handle validation errors from backend
                    const errorMessages = data.detail.details.map((detail: any) => detail.message)
                    setError(errorMessages.join('. '))
                } else {
                    setError(data.detail?.message || 'An error occurred. Please try again.')
                }
            }
        } catch (err) {
            setError('Network error. Please check your connection and try again.')
        } finally {
            setLoading(false)
        }
    }

    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background px-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                            <CheckCircle className="w-6 h-6 text-green-600" />
                        </div>
                        <CardTitle className="text-2xl">Password Reset Successful</CardTitle>
                        <CardDescription>
                            Your password has been successfully updated
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                <p className="text-sm text-green-800">
                                    Your password has been changed and all existing sessions have been logged out for security.
                                </p>
                            </div>
                            <Link href="/login">
                                <Button className="w-full">
                                    Continue to Login
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        )
    }

    if (!token) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background px-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                            <XCircle className="w-6 h-6 text-red-600" />
                        </div>
                        <CardTitle className="text-2xl">Invalid Reset Link</CardTitle>
                        <CardDescription>
                            This password reset link is invalid or has expired
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="p-3 text-sm bg-muted rounded">
                                Password reset links expire after 1 hour for security reasons.
                            </div>
                            <div className="flex flex-col space-y-3">
                                <Link href="/forgot-password">
                                    <Button className="w-full">
                                        Request New Reset Link
                                    </Button>
                                </Link>
                                <Link href="/login">
                                    <Button variant="outline" className="w-full">
                                        Back to Login
                                    </Button>
                                </Link>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <CardTitle className="text-2xl">Set New Password</CardTitle>
                    <CardDescription>
                        Enter your new password below
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div className="p-3 text-sm text-destructive-foreground bg-destructive/10 border border-destructive/20 rounded">
                                {error}
                            </div>
                        )}

                        <div className="space-y-2">
                            <Label htmlFor="password">New Password</Label>
                            <div className="relative">
                                <Input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="Enter new password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    disabled={loading}
                                    required
                                    autoFocus
                                    className="pr-10"
                                />
                                <button
                                    type="button"
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                            
                            {password && (
                                <div className="text-xs space-y-1">
                                    <p className="font-medium">Password requirements:</p>
                                    {[
                                        'At least 8 characters long',
                                        'One uppercase letter',
                                        'One lowercase letter', 
                                        'One number'
                                    ].map((requirement, index) => {
                                        const isValid = !validationErrors.includes(requirement)
                                        return (
                                            <div key={index} className="flex items-center space-x-2">
                                                {isValid ? (
                                                    <CheckCircle className="w-3 h-3 text-green-600" />
                                                ) : (
                                                    <XCircle className="w-3 h-3 text-red-500" />
                                                )}
                                                <span className={isValid ? 'text-green-600' : 'text-red-500'}>
                                                    {requirement}
                                                </span>
                                            </div>
                                        )
                                    })}
                                </div>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword">Confirm New Password</Label>
                            <div className="relative">
                                <Input
                                    id="confirmPassword"
                                    type={showConfirmPassword ? 'text' : 'password'}
                                    placeholder="Confirm new password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    disabled={loading}
                                    required
                                    className="pr-10"
                                />
                                <button
                                    type="button"
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                >
                                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                            
                            {confirmPassword && password !== confirmPassword && (
                                <div className="flex items-center space-x-2 text-xs">
                                    <XCircle className="w-3 h-3 text-red-500" />
                                    <span className="text-red-500">Passwords do not match</span>
                                </div>
                            )}
                        </div>

                        <Button 
                            type="submit" 
                            className="w-full" 
                            disabled={loading || validationErrors.length > 0 || password !== confirmPassword}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Updating Password...
                                </>
                            ) : (
                                'Update Password'
                            )}
                        </Button>

                        <div className="text-center">
                            <Link 
                                href="/login" 
                                className="text-sm text-primary hover:underline"
                            >
                                Back to Login
                            </Link>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    )
}

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-background">
                <Loader2 className="w-8 h-8 animate-spin" />
            </div>
        }>
            <ResetPasswordContent />
        </Suspense>
    )
}