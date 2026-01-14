import { ReactNode } from "react";
import ModeToggle from "./mode-toggle";

const ModeWrapper = ({ children }: { children: ReactNode }) => {
  return (
    <div>
      <div className="fixed top-1 right-32 z-20">
        <ModeToggle />
        {/* <LanguageToggle /> */}
      </div>
      {children}
    </div>
  );
};

export default ModeWrapper;
