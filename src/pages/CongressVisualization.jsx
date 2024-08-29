import React from 'react';
import HouseSeatingChart from '../components/HouseSeatingChart';

const CongressVisualization = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Current US House of Representatives Seating Chart</h1>
      <HouseSeatingChart />
      <p className="mt-4 text-sm text-gray-600">
        Note: This visualization shows the current seating arrangement in the US House of Representatives.
        Each dot represents a member, colored according to their party affiliation (Blue for Democrats, Red for Republicans, Gray for others).
      </p>
    </div>
  );
};

export default CongressVisualization;
