import { useState, useEffect } from 'react'
import { Clock, AlertCircle } from 'lucide-react'

export default function RateLimitCountdown({ initialSeconds }) {
    const [timeLeft, setTimeLeft] = useState(initialSeconds)

    useEffect(() => {
        if (!timeLeft) return

        const intervalId = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    clearInterval(intervalId)
                    return 0
                }
                return prev - 1
            })
        }, 1000)

        return () => clearInterval(intervalId)
    }, [])

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    const percentage = Math.max(0, (timeLeft / initialSeconds) * 100)

    return (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 max-w-md w-full my-2 animate-fade-in relative overflow-hidden">
            {/* Background Progress Bar */}
            <div
                className="absolute bottom-0 left-0 h-1 bg-red-500/30 transition-all duration-1000 ease-linear"
                style={{ width: `${percentage}%` }}
            />

            <div className="flex items-start gap-3 relative z-10">
                <div className="p-2 bg-red-500/10 rounded-full mt-1">
                    <AlertCircle className="w-5 h-5 text-red-400" />
                </div>

                <div className="flex-1">
                    <h3 className="text-red-200 font-medium mb-1">API Rate Limit Reached</h3>
                    <p className="text-red-200/70 text-sm mb-3">
                        To ensure fair usage, please wait before sending more requests.
                    </p>

                    <div className="flex items-center gap-3">
                        <div className="bg-[#151616] border border-red-500/20 rounded-md px-3 py-1.5 flex items-center gap-2">
                            <Clock className="w-4 h-4 text-red-400 animate-pulse" />
                            <span className="font-mono text-lg font-medium text-red-100">
                                {formatTime(timeLeft)}
                            </span>
                        </div>
                        <span className="text-xs text-red-200/50">
                            {timeLeft > 0 ? "resuming soon..." : "ready to retry"}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}
