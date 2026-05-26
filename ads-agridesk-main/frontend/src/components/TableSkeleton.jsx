export default function TableSkeleton({ rows = 5 }) {
  return (
    <div className="w-full">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-ivory border-b border-sepia-200">
              <th className="py-4 px-6"><div className="h-3 w-16 bg-sepia-200 rounded animate-pulse"></div></th>
              <th className="py-4 px-6"><div className="h-3 w-32 bg-sepia-200 rounded animate-pulse"></div></th>
              <th className="py-4 px-6"><div className="h-3 w-24 bg-sepia-200 rounded animate-pulse"></div></th>
              <th className="py-4 px-6 text-right"><div className="h-3 w-20 bg-sepia-200 rounded animate-pulse ml-auto"></div></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-sepia-200">
            {Array.from({ length: rows }).map((_, i) => (
              <tr key={i}>
                <td className="py-5 px-6">
                  <div className="h-4 w-20 bg-ivory-dark rounded animate-pulse"></div>
                </td>
                <td className="py-5 px-6 space-y-2">
                  <div className="h-4 w-48 bg-ivory-dark rounded animate-pulse"></div>
                  <div className="h-3 w-32 bg-sepia-200 rounded animate-pulse"></div>
                </td>
                <td className="py-5 px-6">
                  <div className="h-5 w-24 bg-ivory-dark rounded-full animate-pulse"></div>
                </td>
                <td className="py-5 px-6 flex justify-end gap-2">
                  <div className="h-8 w-16 bg-ivory-dark rounded animate-pulse"></div>
                  <div className="h-8 w-16 bg-ivory-dark rounded animate-pulse"></div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
