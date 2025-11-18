"use client"

export function ScenarioCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
        <div className="w-16 h-6 bg-gray-200 rounded-full"></div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="w-3/4 h-5 bg-gray-200 rounded"></div>
        <div className="w-full h-4 bg-gray-200 rounded"></div>
        <div className="w-2/3 h-4 bg-gray-200 rounded"></div>
      </div>
      
      <div className="flex gap-2 mb-4">
        <div className="w-12 h-5 bg-gray-200 rounded-full"></div>
        <div className="w-16 h-5 bg-gray-200 rounded-full"></div>
        <div className="w-14 h-5 bg-gray-200 rounded-full"></div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex justify-between">
          <div className="w-20 h-4 bg-gray-200 rounded"></div>
          <div className="w-12 h-4 bg-gray-200 rounded"></div>
        </div>
        <div className="flex justify-between">
          <div className="w-16 h-4 bg-gray-200 rounded"></div>
          <div className="w-20 h-4 bg-gray-200 rounded"></div>
        </div>
      </div>
      
      <div className="flex gap-2 pt-4 border-t border-gray-100">
        <div className="flex-1 h-8 bg-gray-200 rounded"></div>
        <div className="flex-1 h-8 bg-gray-200 rounded"></div>
        <div className="w-10 h-8 bg-gray-200 rounded"></div>
      </div>
    </div>
  )
}

export function ScenarioListSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: 6 }, (_, i) => (
        <ScenarioCardSkeleton key={i} />
      ))}
    </div>
  )
}