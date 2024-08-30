import { HomeIcon, PieChartIcon, UsersIcon } from "lucide-react";
import Index from "./pages/Index.jsx";
import CongressVisualization from "./pages/CongressVisualization.jsx";
import SenateVisualization from "./pages/SenateVisualization.jsx";

/**
 * Central place for defining the navigation items. Used for navigation components and routing.
 */
export const navItems = [
  {
    title: "Home",
    to: "/",
    icon: <HomeIcon className="h-4 w-4" />,
    page: <Index />,
  },
  {
    title: "House Visualization",
    to: "/house",
    icon: <PieChartIcon className="h-4 w-4" />,
    page: <CongressVisualization />,
  },
  {
    title: "Senate Visualization",
    to: "/senate",
    icon: <UsersIcon className="h-4 w-4" />,
    page: <SenateVisualization />,
  },
];
