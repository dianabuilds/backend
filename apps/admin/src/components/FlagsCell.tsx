import { Eye, Globe, Star, ThumbsUp } from 'lucide-react';

export type FlagField = 'is_visible' | 'is_public' | 'premium_only' | 'is_recommendable';

type FlagsCellProps = {
  value: Record<FlagField, boolean | undefined>;
  onToggle: (field: FlagField) => void;
  disabledVisible?: boolean;
};

export default function FlagsCell({ value, onToggle, disabledVisible }: FlagsCellProps) {
  const iconClass = (active: boolean) => (active ? 'text-blue-600' : 'text-gray-400');
  return (
    <div className="flex items-center justify-center gap-1">
      <button
        type="button"
        onClick={() => onToggle('is_visible')}
        disabled={disabledVisible}
        title={value.is_visible ? 'Visible' : 'Hidden'}
        className={iconClass(!!value.is_visible)}
      >
        <Eye className="h-4 w-4" />
      </button>
      <button
        type="button"
        onClick={() => onToggle('is_public')}
        title={value.is_public ? 'Public' : 'Private'}
        className={iconClass(!!value.is_public)}
      >
        <Globe className="h-4 w-4" />
      </button>
      <button
        type="button"
        onClick={() => onToggle('premium_only')}
        title={value.premium_only ? 'Premium only' : 'Free'}
        className={iconClass(!!value.premium_only)}
      >
        <Star className="h-4 w-4" />
      </button>
      <button
        type="button"
        onClick={() => onToggle('is_recommendable')}
        title={value.is_recommendable ? 'Recommendable' : 'Not recommendable'}
        className={iconClass(!!value.is_recommendable)}
      >
        <ThumbsUp className="h-4 w-4" />
      </button>
    </div>
  );
}
