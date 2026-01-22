import { useAuthStore } from '../api/auth-store'

export default function DashboardPage() {
  const { username, tenantId, logout } = useAuthStore()

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-800">
            Renty Dynamic Pricing
          </h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {username} (Tenant: {tenantId})
            </span>
            <button
              onClick={logout}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Branch Selector */}
        <div className="mb-6 flex gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Branch
            </label>
            <select className="px-3 py-2 border border-gray-300 rounded-md min-w-[200px]">
              <option>Select Branch...</option>
              {/* Will be populated from API */}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              className="px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>

        {/* 6 Category Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Category {i}
              </h3>
              <div className="grid grid-cols-2 gap-4 mb-4">
                {/* Base Prices */}
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">
                    Base Prices
                  </h4>
                  <div className="space-y-1 text-sm">
                    <div>Daily: <span className="font-medium">--</span></div>
                    <div>Weekly: <span className="font-medium">--</span></div>
                    <div>Monthly: <span className="font-medium">--</span></div>
                  </div>
                </div>
                {/* Recommended Prices */}
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">
                    Recommended
                  </h4>
                  <div className="space-y-1 text-sm">
                    <div>Daily: <span className="font-medium text-green-600">--</span></div>
                    <div>Weekly: <span className="font-medium text-green-600">--</span></div>
                    <div>Monthly: <span className="font-medium text-green-600">--</span></div>
                  </div>
                </div>
              </div>
              {/* Premium/Discount Badge */}
              <div className="mb-4">
                <span className="inline-block bg-gray-100 text-gray-600 px-2 py-1 rounded text-sm">
                  -- %
                </span>
              </div>
              {/* Actions */}
              <div className="flex gap-2">
                <button className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700">
                  Approve
                </button>
                <button className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">
                  Skip
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* 30-Day Window Placeholder */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            30-Day Forecast Window
          </h3>
          <div className="text-gray-500 text-center py-8">
            Select a branch and date to view recommendations
          </div>
        </div>
      </main>
    </div>
  )
}
