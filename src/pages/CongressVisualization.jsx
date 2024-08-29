import React from 'react';
import HouseSeatingChart from '../components/HouseSeatingChart';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

const CongressVisualization = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Current US House of Representatives Seating Chart</h1>
      <Alert className="mb-4">
        <AlertTitle>Important</AlertTitle>
        <AlertDescription>
          To use this visualization, you need to add your Congress.gov API key to the .env file in the root of your project.
          Create a file named .env and add the following line:
          VITE_CONGRESS_API_KEY=your_actual_api_key_here
          Replace 'your_actual_api_key_here' with your Congress.gov API key.
        </AlertDescription>
      </Alert>
      <HouseSeatingChart />
      <p className="mt-4 text-sm text-gray-600">
        Note: This visualization shows the current seating arrangement in the US House of Representatives.
        Each dot represents a member, colored according to their party affiliation (Blue for Democrats, Red for Republicans, Gray for others).
      </p>
    </div>
  );
};

export default CongressVisualization;
