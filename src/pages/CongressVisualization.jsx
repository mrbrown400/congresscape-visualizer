import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
  { chamber: 'House', Democrats: 213, Republicans: 222 },
  { chamber: 'Senate', Democrats: 51, Republicans: 49 },
];

const CongressVisualization = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Current US Congress Visualization</h1>
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="chamber" type="category" />
            <Tooltip />
            <Legend />
            <Bar dataKey="Democrats" fill="#0000FF" />
            <Bar dataKey="Republicans" fill="#FF0000" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-4 text-sm text-gray-600">
        Note: This visualization shows the current party distribution in the US Congress as of 2023.
        The data may not reflect any recent changes or special circumstances.
      </p>
    </div>
  );
};

export default CongressVisualization;