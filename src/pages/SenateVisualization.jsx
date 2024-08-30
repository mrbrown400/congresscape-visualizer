import React from 'react';
import SenateSeatingChart from '../components/SenateSeatingChart';

const SenateVisualization = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Current US Senate Seating Chart</h1>
      <SenateSeatingChart />
      <p className="mt-4 text-sm text-gray-600">
        Note: This visualization shows the current seating arrangement in the US Senate.
        Each dot represents a senator, colored according to their party affiliation (Blue for Democrats, Red for Republicans, Gray for others).
      </p>
    </div>
  );
};

export default SenateVisualization;