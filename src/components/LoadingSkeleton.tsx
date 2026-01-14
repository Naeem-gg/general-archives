import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

interface LoadingSkeletonProps {
  type?: "card" | "list" | "table" | "detail" | "full";
  count?: number;
  showSpinner?: boolean;
  text?: string;
  className?: string;
}

export default function LoadingSkeleton({
  type = "card",
  count = 3,
  showSpinner = true,
  text = "Loading data...",
  className = "",
}: LoadingSkeletonProps) {
  const [progress, setProgress] = useState(0);

  // Simulated progress animation
  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer);
          return 100;
        }
        return prev + 1;
      });
    }, 50);

    return () => clearInterval(timer);
  }, []);

  // Shimmer animation variants
  const shimmer = {
    hidden: { opacity: 0.3 },
    visible: {
      opacity: 0.6,
      transition: {
        repeat: Number.POSITIVE_INFINITY,
        repeatType: "reverse" as const,
        duration: 1.5,
      },
    },
  };

  // Render different skeleton types
  const renderSkeleton = () => {
    switch (type) {
      case "card":
        return (
          <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: count }).map((_, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.1 }}
                className="bg-card/30 backdrop-blur-sm border border-border/50 rounded-lg overflow-hidden shadow-sm"
              >
                <div className="h-40 relative overflow-hidden">
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/10 to-transparent"
                    style={{ transform: "translateX(-100%)" }}
                    transition={{
                      repeat: Number.POSITIVE_INFINITY,
                      repeatType: "loop",
                      duration: 2,
                      ease: "linear",
                    }}
                  />
                  <div className="absolute inset-0 bg-muted/30" />
                </div>
                <div className="p-4 space-y-3">
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-6 bg-muted/50 rounded-md w-3/4"
                  />
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-4 bg-muted/40 rounded-md w-full"
                  />
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-4 bg-muted/40 rounded-md w-2/3"
                  />
                </div>
              </motion.div>
            ))}
          </div>
        );

      case "list":
        return (
          <div className="space-y-3 w-full">
            {Array.from({ length: count }).map((_, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: i * 0.05 }}
                className="flex items-center p-3 bg-card/30 backdrop-blur-sm border border-border/50 rounded-lg"
              >
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="w-10 h-10 rounded-full bg-muted/50 mr-3"
                />
                <div className="flex-1 space-y-2">
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-4 bg-muted/50 rounded-md w-1/3"
                  />
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-3 bg-muted/40 rounded-md w-1/2"
                  />
                </div>
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="w-20 h-8 bg-muted/30 rounded-md"
                />
              </motion.div>
            ))}
          </div>
        );

      case "table":
        return (
          <div className="w-full bg-card/30 backdrop-blur-sm border border-border/50 rounded-lg overflow-hidden">
            <div className="p-4 border-b border-border/50 bg-muted/20">
              <div className="grid grid-cols-4 gap-4">
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-6 bg-muted/50 rounded-md"
                />
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-6 bg-muted/50 rounded-md"
                />
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-6 bg-muted/50 rounded-md"
                />
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-6 bg-muted/50 rounded-md"
                />
              </div>
            </div>
            <div className="divide-y divide-border/50">
              {Array.from({ length: count }).map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="p-4"
                >
                  <div className="grid grid-cols-4 gap-4">
                    <motion.div
                      variants={shimmer}
                      initial="hidden"
                      animate="visible"
                      className="h-4 bg-muted/40 rounded-md"
                    />
                    <motion.div
                      variants={shimmer}
                      initial="hidden"
                      animate="visible"
                      className="h-4 bg-muted/40 rounded-md"
                    />
                    <motion.div
                      variants={shimmer}
                      initial="hidden"
                      animate="visible"
                      className="h-4 bg-muted/40 rounded-md"
                    />
                    <motion.div
                      variants={shimmer}
                      initial="hidden"
                      animate="visible"
                      className="h-4 bg-muted/40 rounded-md"
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        );

      case "detail":
        return (
          <div className="bg-card/30 backdrop-blur-sm border border-border/50 rounded-lg overflow-hidden shadow-sm">
            <div className="p-6 border-b border-border/50">
              <motion.div
                variants={shimmer}
                initial="hidden"
                animate="visible"
                className="h-8 bg-muted/50 rounded-md w-1/3 mb-4"
              />
              <motion.div
                variants={shimmer}
                initial="hidden"
                animate="visible"
                className="h-4 bg-muted/40 rounded-md w-2/3"
              />
            </div>
            <div className="p-6 space-y-6">
              <div className="space-y-3">
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-5 bg-muted/50 rounded-md w-1/4"
                />
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-20 bg-muted/30 rounded-md w-full"
                />
              </div>
              <div className="space-y-3">
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-5 bg-muted/50 rounded-md w-1/4"
                />
                <div className="grid grid-cols-2 gap-4">
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-10 bg-muted/30 rounded-md"
                  />
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-10 bg-muted/30 rounded-md"
                  />
                </div>
              </div>
              <div className="space-y-3">
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-5 bg-muted/50 rounded-md w-1/4"
                />
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-32 bg-muted/30 rounded-md w-full"
                />
              </div>
            </div>
          </div>
        );

      case "full":
        return (
          <div className="w-full h-full flex flex-col">
            <div className="h-16 bg-card/30 backdrop-blur-sm border-b border-border/50 flex items-center px-6 mb-6">
              <motion.div
                variants={shimmer}
                initial="hidden"
                animate="visible"
                className="h-8 bg-muted/50 rounded-md w-1/4"
              />
              <div className="ml-auto flex space-x-3">
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-8 w-8 bg-muted/40 rounded-md"
                />
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-8 w-24 bg-muted/40 rounded-md"
                />
              </div>
            </div>
            <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6 px-6">
              <div className="md:col-span-2 space-y-6">
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-64 bg-muted/30 rounded-lg w-full"
                />
                <div className="space-y-3">
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-6 bg-muted/50 rounded-md w-1/3"
                  />
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-4 bg-muted/40 rounded-md w-full"
                  />
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-4 bg-muted/40 rounded-md w-full"
                  />
                  <motion.div
                    variants={shimmer}
                    initial="hidden"
                    animate="visible"
                    className="h-4 bg-muted/40 rounded-md w-3/4"
                  />
                </div>
              </div>
              <div className="space-y-6">
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-40 bg-muted/30 rounded-lg w-full"
                />
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-40 bg-muted/30 rounded-lg w-full"
                />
                <motion.div
                  variants={shimmer}
                  initial="hidden"
                  animate="visible"
                  className="h-40 bg-muted/30 rounded-lg w-full"
                />
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {showSpinner && (
        <div className="flex flex-col items-center justify-center mb-8 mt-4">
          <div className="relative h-24 w-24 flex items-center justify-center">
            {/* Circular progress indicator */}
            <svg
              className="absolute"
              width="100"
              height="100"
              viewBox="0 0 100 100"
            >
              <circle
                className="text-muted/20 stroke-current"
                strokeWidth="8"
                stroke="currentColor"
                fill="transparent"
                r="42"
                cx="50"
                cy="50"
              />
              <circle
                className="text-primary stroke-current"
                strokeWidth="8"
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                r="42"
                cx="50"
                cy="50"
                strokeDasharray="264"
                strokeDashoffset={264 - (progress * 264) / 100}
                transform="rotate(-90 50 50)"
              />
            </svg>

            <motion.div
              animate={{ rotate: 360 }}
              transition={{
                duration: 2,
                repeat: Number.POSITIVE_INFINITY,
                ease: "linear",
              }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <Loader2 className="h-10 w-10 text-primary" />
            </motion.div>

            <div className="absolute text-sm font-medium">{progress}%</div>
          </div>
          <p className="text-muted-foreground mt-4 text-center font-medium">
            {text}
          </p>
        </div>
      )}

      <div className={showSpinner ? "mt-4" : ""}>{renderSkeleton()}</div>
    </div>
  );
}
