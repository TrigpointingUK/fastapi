interface BadgeProps {
  children: React.ReactNode;
  variant?: "good" | "damaged" | "missing" | "unknown" | "default";
  className?: string;
}

export default function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  const variantClasses = {
    good: "bg-green-100 text-green-800",
    damaged: "bg-yellow-100 text-yellow-800",
    missing: "bg-red-100 text-red-800",
    unknown: "bg-gray-100 text-gray-800",
    default: "bg-blue-100 text-blue-800",
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
}

