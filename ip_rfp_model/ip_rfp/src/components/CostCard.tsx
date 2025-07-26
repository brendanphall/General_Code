interface CostCardProps {
  title: string;
  value: string;
  subtitle?: string;
  gradient?: string;
}

export default function CostCard({
  title,
  value,
  subtitle,
  gradient = "from-blue-500 to-purple-600"
}: CostCardProps) {
  return (
    <div className={`bg-gradient-to-r ${gradient} text-white p-4 rounded-xl shadow-lg`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm opacity-90">{title}</div>
      {subtitle && <div className="text-xs opacity-75 mt-1">{subtitle}</div>}
    </div>
  );
}