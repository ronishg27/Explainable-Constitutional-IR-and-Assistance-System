export default function ConfidenceBadge({ score }) {
  if (score == null) return null;

  let label, dotColor, textColor, bgColor;
  if (score >= 70) {
    label = 'High Confidence';
    dotColor = 'bg-green-500';
    textColor = 'text-green-800';
    bgColor = 'bg-green-50';
  } else if (score >= 40) {
    label = 'Medium Confidence';
    dotColor = 'bg-amber-500';
    textColor = 'text-amber-800';
    bgColor = 'bg-amber-50';
  } else {
    label = 'Low Confidence';
    dotColor = 'bg-red-500';
    textColor = 'text-red-800';
    bgColor = 'bg-red-50';
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${bgColor} px-2.5 py-1 ${textColor} text-xs font-medium`}
    >
      <span className={`inline-block w-1.5 h-1.5 rounded-full ${dotColor}`} />
      {label} ({score}%)
    </span>
  );
}
