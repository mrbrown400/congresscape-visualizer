import { HomeIcon, PieChartIcon } from "lucide-react";
import Index from "./pages/Index.jsx";
import CongressVisualization from "./pages/CongressVisualization.jsx";

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
    title: "Congress Visualization",
    to: "/congress",
    icon: <PieChartIcon className="h-4 w-4" />,
    page: <CongressVisualization />,
  },
];
