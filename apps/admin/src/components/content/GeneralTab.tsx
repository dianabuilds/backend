import FieldCover from '../fields/FieldCover';
import FieldTags from '../fields/FieldTags';
import FieldTitle from '../fields/FieldTitle';
import type { GeneralTabProps } from './GeneralTab.helpers';

export default function GeneralTab({
  title = '',
  tags = [],
  coverUrl = null,
  // Summary удалён из интерфейса формы: оставляем значения в пропсах, но не используем
  titleError = null,
  coverError = null,
  onTitleChange,
  titleRef,
  onTagsChange,
  onCoverChange,
}: GeneralTabProps) {
  return (
    <div className="space-y-4">
      <FieldTitle
        ref={titleRef}
        value={title}
        onChange={onTitleChange ?? (() => {})}
        error={titleError}
      />
      {/* Показываем Cover всегда под Title. Если обработчик не передан — noop */}
      <FieldCover value={coverUrl} onChange={onCoverChange ?? (() => {})} error={coverError} />
      <FieldTags value={tags} onChange={onTagsChange ?? (() => {})} />
    </div>
  );
}
