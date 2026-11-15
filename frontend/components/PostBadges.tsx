const SIZES = {
  small: "px-1.5 py-px text-[0.6rem] tracking-[0.08em]",
  large: "px-2 py-1 text-xs",
};

interface Props {
  clusterHash: string | null;
  deleted: number;
  size?: keyof typeof SIZES;
}

export default function PostBadges({ clusterHash, deleted, size = "small" }: Props) {
  const badge = `border font-bold whitespace-nowrap ${SIZES[size]}`;
  return (
    <>
      {clusterHash && <span className={`${badge} border-border text-secondary`}>topic: #{clusterHash}</span>}
      {deleted === 1 && <span className={`${badge} border-red-500 bg-red-500 text-background`}>DELETED</span>}
    </>
  );
}
