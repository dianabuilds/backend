interface Props {
  role: string;
  isActive: 'any' | 'true' | 'false';
  isPremium: 'any' | 'true' | 'false';
  createdFrom: string;
  createdTo: string;
  onRoleChange: (v: string) => void;
  onIsActiveChange: (v: 'any' | 'true' | 'false') => void;
  onIsPremiumChange: (v: 'any' | 'true' | 'false') => void;
  onCreatedFromChange: (v: string) => void;
  onCreatedToChange: (v: string) => void;
}

export default function NotificationFilters({
  role,
  isActive,
  isPremium,
  createdFrom,
  createdTo,
  onRoleChange,
  onIsActiveChange,
  onIsPremiumChange,
  onCreatedFromChange,
  onCreatedToChange,
}: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
      <div className="flex flex-col">
        <label className="text-sm text-gray-600">Role</label>
        <select
          className="border rounded px-2 py-1"
          value={role}
          onChange={(e) => onRoleChange(e.target.value)}
        >
          <option value="">any</option>
          <option value="user">user</option>
          <option value="moderator">moderator</option>
          <option value="admin">admin</option>
        </select>
      </div>
      <div className="flex flex-col">
        <label className="text-sm text-gray-600">Active</label>
        <select
          className="border rounded px-2 py-1"
          value={isActive}
          onChange={(e) => onIsActiveChange(e.target.value as Props['isActive'])}
        >
          <option value="any">any</option>
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      </div>
      <div className="flex flex-col">
        <label className="text-sm text-gray-600">Premium</label>
        <select
          className="border rounded px-2 py-1"
          value={isPremium}
          onChange={(e) => onIsPremiumChange(e.target.value as Props['isPremium'])}
        >
          <option value="any">any</option>
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      </div>
      <div className="flex flex-col">
        <label className="text-sm text-gray-600">Created from</label>
        <input
          type="datetime-local"
          className="border rounded px-2 py-1"
          value={createdFrom}
          onChange={(e) => onCreatedFromChange(e.target.value)}
        />
      </div>
      <div className="flex flex-col">
        <label className="text-sm text-gray-600">Created to</label>
        <input
          type="datetime-local"
          className="border rounded px-2 py-1"
          value={createdTo}
          onChange={(e) => onCreatedToChange(e.target.value)}
        />
      </div>
    </div>
  );
}
