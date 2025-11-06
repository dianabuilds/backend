import React from 'react';
import {
  Badge,
  Button,
  Card,
  Dialog,
  Input,
  Select,
  Spinner,
  Switch,
  Textarea,
} from '@ui';
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  type DragEndEvent,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { AlertTriangle, Edit3, GripVertical, Plus, Trash2 } from '@icons';
import {
  HEADER_CTA_STYLE_OPTIONS,
  HEADER_LINK_TARGET_OPTIONS,
  HEADER_VARIANT_OPTIONS,
  createDefaultCta,
  createDefaultHeaderConfig,
  createDefaultLogo,
  createDefaultMenuGroup,
  createDefaultMenuItem,
  ensureHeaderConfig,
  type HeaderCta,
  type HeaderCtaStyle,
  type HeaderLayoutVariant,
  type HeaderMenuGroup,
  type HeaderMenuItem,
  type SiteHeaderConfig,
  cloneMenuGroup,
  cloneMenuItem,
} from '../schemas/siteHeader';

type SiteBlockHeaderFormProps = {
  value: SiteHeaderConfig | null;
  disabled?: boolean;
  onChange: (next: SiteHeaderConfig) => void;
  remoteIssues?: HeaderValidationIssue[];
  generalMessages?: string[];
  validationLoading?: boolean;
};

export type HeaderValidationIssue = {
  path: string;
  message: string;
};

type MenuGroupKey = 'primary' | 'secondary' | 'utility' | 'mobile.menu';

type MenuGroupDescriptor = {
  key: MenuGroupKey;
  label: string;
  description?: string;
  allowChildren: boolean;
};

const MENU_GROUPS: MenuGroupDescriptor[] = [
  {
    key: 'primary',
    label: 'Основное меню',
    description: 'Пункты навигации, размещённые в хедере слева направо.',
    allowChildren: true,
  },
  {
    key: 'secondary',
    label: 'Второстепенное меню',
    description: 'Дополнительные ссылки (например, тарифы, блог, партнёры).',
    allowChildren: true,
  },
  {
    key: 'utility',
    label: 'Utility меню',
    description: 'Ссылки на авторизацию, поддержку, переключение языка.',
    allowChildren: false,
  },
  {
    key: 'mobile.menu',
    label: 'Мобильное меню',
    description: 'Пункты, отображаемые внутри бургер-меню.',
    allowChildren: true,
  },
];

const DRAG_ACTIVATION_CONSTRAINT = { distance: 6 } as const;

type MenuItemErrors = Partial<Record<'id' | 'label' | 'href', string>>;

function getMenuGroup(config: SiteHeaderConfig, key: MenuGroupKey): HeaderMenuGroup {
  const navigation = config.navigation ?? {
    primary: createDefaultMenuGroup(),
    secondary: createDefaultMenuGroup(),
    utility: createDefaultMenuGroup(),
    cta: null,
    mobile: {
      menu: createDefaultMenuGroup(),
      cta: null,
    },
  };
  switch (key) {
    case 'primary':
      return navigation.primary ?? createDefaultMenuGroup();
    case 'secondary':
      return navigation.secondary ?? createDefaultMenuGroup();
    case 'utility':
      return navigation.utility ?? createDefaultMenuGroup();
    case 'mobile.menu':
      return navigation.mobile?.menu ?? createDefaultMenuGroup();
    default:
      return createDefaultMenuGroup();
  }
}

function setMenuGroup(
  config: SiteHeaderConfig,
  key: MenuGroupKey,
  group: HeaderMenuGroup,
): SiteHeaderConfig {
  if (key === 'mobile.menu') {
    return {
      ...config,
      navigation: {
        ...config.navigation,
        mobile: {
          menu: group,
          cta: config.navigation.mobile?.cta ?? null,
        },
      },
    };
  }
  return {
    ...config,
    navigation: {
      ...config.navigation,
      [key]: group,
    },
  };
}

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="space-y-4 p-5">
      <div>
        <div className="text-sm font-semibold text-gray-900 dark:text-white">{title}</div>
        {description ? <p className="text-xs text-gray-500 dark:text-dark-200">{description}</p> : null}
      </div>
      <div className="space-y-4">{children}</div>
    </Card>
  );
}

function FieldError({ message }: { message?: string }) {
  if (!message) {
    return null;
  }
  return <div className="text-xs text-rose-600 dark:text-rose-300">{message}</div>;
}

export function validateHeaderConfig(config: SiteHeaderConfig): HeaderValidationIssue[] {
  const issues: HeaderValidationIssue[] = [];
  if (!config.branding.title.trim()) {
    issues.push({ path: 'branding.title', message: 'Укажите название' });
  }
  if (!config.branding.href.trim()) {
    issues.push({ path: 'branding.href', message: 'Укажите ссылку' });
  }
  if (!config.branding.logo?.light?.trim()) {
    issues.push({ path: 'branding.logo.light', message: 'Добавьте ссылку на логотип (light)' });
  }

  const primary = config.navigation.primary ?? [];
  primary.forEach((item, index) => {
    if (!item.label.trim()) {
      issues.push({
        path: `navigation.primary.${index}.label`,
        message: 'Заполните заголовок',
      });
    }
    if (!item.href.trim()) {
      issues.push({
        path: `navigation.primary.${index}.href`,
        message: 'Укажите ссылку',
      });
    }
    if (!item.id.trim()) {
      issues.push({
        path: `navigation.primary.${index}.id`,
        message: 'Добавьте идентификатор',
      });
    }
  });

  const cta = config.navigation.cta;
  if (cta && (!cta.label.trim() || !cta.href.trim())) {
    if (!cta.label.trim()) {
      issues.push({ path: 'navigation.cta.label', message: 'Укажите текст кнопки' });
    }
    if (!cta.href.trim()) {
      issues.push({ path: 'navigation.cta.href', message: 'Укажите ссылку' });
    }
  }

  return issues;
}

function hasIssue(issues: HeaderValidationIssue[], path: string): HeaderValidationIssue | undefined {
  return issues.find((issue) => issue.path === path);
}
type SortableMenuItemRowProps = {
  item: HeaderMenuItem;
  index: number;
  sortableId: string;
  hasError: boolean;
  disabled?: boolean;
  onEdit: () => void;
  onRemove: () => void;
};

function SortableMenuItemRow({
  item,
  index,
  sortableId,
  hasError,
  disabled,
  onEdit,
  onRemove,
}: SortableMenuItemRowProps): React.ReactElement {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: sortableId });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const hasChildren = Array.isArray(item.children) && item.children.length > 0;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={[
        'flex items-start gap-3 rounded-lg border bg-white p-3 shadow-sm transition',
        hasError
          ? 'border-amber-300 bg-amber-50/60'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-md dark:border-dark-600 dark:bg-dark-800',
        isDragging ? 'ring-2 ring-primary-300/40' : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <button
        type="button"
        aria-label={`Переместить пункт ${item.label || index + 1}`}
        className="mt-1 inline-flex h-8 w-8 shrink-0 cursor-grab items-center justify-center rounded-md border border-gray-200 bg-gray-50 text-gray-500 transition hover:border-gray-300 hover:text-gray-700 disabled:cursor-not-allowed"
        {...attributes}
        {...listeners}
        disabled={disabled}
      >
        <GripVertical className="h-4 w-4" />
      </button>

      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate font-medium text-gray-900 dark:text-dark-50">
            {item.label.trim() || `Пункт ${index + 1}`}
          </span>
          {hasChildren ? <Badge color="primary">Подменю · {item.children?.length ?? 0}</Badge> : null}
          {hasError ? <Badge color="warning">Есть ошибки</Badge> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
          <span className="font-mono">{item.id || '—'}</span>
          <span className="opacity-40">•</span>
          <span className="truncate">{item.href || '—'}</span>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <Button
          type="button"
          size="icon"
          variant="ghost"
          aria-label="Редактировать пункт"
          onClick={onEdit}
          disabled={disabled}
        >
          <Edit3 className="h-4 w-4" />
        </Button>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          aria-label="Удалить пункт"
          onClick={onRemove}
          disabled={disabled}
          className="text-rose-600 hover:text-rose-700"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

type MenuItemsListProps = {
  items: HeaderMenuGroup;
  groupKey: MenuGroupKey;
  disabled?: boolean;
  itemErrors: boolean[];
  onReorder: (next: HeaderMenuGroup) => void;
  onEdit: (index: number) => void;
  onRemove: (index: number) => void;
  onAdd: () => void;
};

function MenuItemsList({
  items,
  groupKey,
  disabled,
  itemErrors,
  onReorder,
  onEdit,
  onRemove,
  onAdd,
}: MenuItemsListProps): React.ReactElement {
  const itemIds = React.useMemo(
    () =>
      items.map((item, index) => {
        const baseId = item.id.trim();
        return baseId ? `${groupKey}-${baseId}` : `${groupKey}-index-${index}`;
      }),
    [groupKey, items],
  );

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: DRAG_ACTIVATION_CONSTRAINT }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleDragEnd = React.useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) {
        return;
      }
      const oldIndex = itemIds.indexOf(String(active.id));
      const newIndex = itemIds.indexOf(String(over.id));
      if (oldIndex === -1 || newIndex === -1) {
        return;
      }
      onReorder(arrayMove(items, oldIndex, newIndex));
    },
    [itemIds, items, onReorder],
  );

  return (
    <div className="space-y-3">
      {items.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-500 dark:border-dark-600 dark:bg-dark-800/40 dark:text-dark-200">
          Нет пунктов меню. Добавьте первый элемент.
        </div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={itemIds} strategy={verticalListSortingStrategy}>
            <div className="space-y-3">
              {items.map((item, index) => (
                <SortableMenuItemRow
                  key={itemIds[index]}
                  item={item}
                  index={index}
                  sortableId={itemIds[index]}
                  hasError={itemErrors[index] ?? false}
                  onEdit={() => onEdit(index)}
                  onRemove={() => onRemove(index)}
                  disabled={disabled}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
      <Button type="button" onClick={onAdd} disabled={disabled} variant="outlined" size="sm">
        <Plus className="mr-1 h-4 w-4" />
        Добавить пункт
      </Button>
    </div>
  );
}

type MenuGroupEditorProps = {
  descriptor: MenuGroupDescriptor;
  items: HeaderMenuGroup;
  issues: HeaderValidationIssue[];
  disabled?: boolean;
  onReorder: (group: HeaderMenuGroup) => void;
  onEdit: (index: number) => void;
  onRemove: (index: number) => void;
  onAdd: () => void;
};

function MenuGroupEditor({
  descriptor,
  items,
  issues,
  disabled,
  onReorder,
  onEdit,
  onRemove,
  onAdd,
}: MenuGroupEditorProps): React.ReactElement {
  const pathPrefix = descriptor.key === 'mobile.menu' ? 'navigation.mobile.menu' : `navigation.${descriptor.key}`;

  const itemErrors = React.useMemo(
    () =>
      items.map((_, index) =>
        issues.some((issue) => issue.path.startsWith(`${pathPrefix}.${index}`)),
      ),
    [issues, items, pathPrefix],
  );

  return (
    <Section title={descriptor.label} description={descriptor.description}>
      <MenuItemsList
        items={items}
        groupKey={descriptor.key}
        itemErrors={itemErrors}
        disabled={disabled}
        onReorder={onReorder}
        onEdit={onEdit}
        onRemove={onRemove}
        onAdd={onAdd}
      />
    </Section>
  );
}
function normalizeMenuItemDraft(draft: HeaderMenuItem): HeaderMenuItem {
  const analyticsEvent = draft.analytics?.event?.trim();
  const normalizedAnalytics = analyticsEvent
    ? {
        event: analyticsEvent,
        context: draft.analytics?.context,
      }
    : undefined;
  const base: HeaderMenuItem = {
    ...draft,
    id: draft.id.trim(),
    label: draft.label.trim(),
    href: draft.href.trim(),
    badge: draft.badge?.trim() || null,
    icon: draft.icon?.trim() || null,
    description: draft.description?.trim() || null,
    ...(normalizedAnalytics ? { analytics: normalizedAnalytics } : {}),
  };
  if (!normalizedAnalytics && 'analytics' in base) {
    delete (base as { analytics?: HeaderMenuItem['analytics'] }).analytics;
  }
  if (Array.isArray(base.children) && base.children.length === 0) {
    base.children = null;
  }
  return base;
}

type MenuItemModalProps = {
  open: boolean;
  allowChildren: boolean;
  initial: HeaderMenuItem;
  onSubmit: (next: HeaderMenuItem) => void;
  onClose: () => void;
};

function MenuItemModal({ open, allowChildren, initial, onSubmit, onClose }: MenuItemModalProps): React.ReactElement | null {
  const [draft, setDraft] = React.useState<HeaderMenuItem>(() => cloneMenuItem(initial));
  const [errors, setErrors] = React.useState<MenuItemErrors>({});

  React.useEffect(() => {
    if (open) {
      setDraft(cloneMenuItem(initial));
      setErrors({});
    }
  }, [initial, open]);

  const handleChange = (key: keyof HeaderMenuItem, value: string) => {
    setDraft((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleAnalyticsChange = (value: string) => {
    const trimmed = value.trim();
    setDraft((prev) => {
      if (!trimmed) {
        return { ...prev, analytics: undefined };
      }
      return {
        ...prev,
        analytics: {
          event: trimmed,
          context: prev.analytics?.context,
        },
      };
    });
  };

  const children = draft.children ?? [];
  const updateChildren = (next: HeaderMenuGroup) => {
    setDraft((prev) => ({
      ...prev,
      children: next.length ? next : null,
    }));
  };

  const handleChildFieldChange = (index: number, key: keyof HeaderMenuItem, value: string) => {
    updateChildren(
      children.map((child, childIndex) =>
        childIndex === index
          ? {
              ...child,
              [key]: value,
            }
          : child,
      ),
    );
  };

  const handleAddChild = () => {
    updateChildren([...children, { ...createDefaultMenuItem(), children: null }]);
  };

  const handleRemoveChild = (index: number) => {
    updateChildren(children.filter((_, i) => i !== index));
  };

  const handleChildReorder = (from: number, to: number) => {
    updateChildren(arrayMove(children, from, to));
  };

  const handleSubmit = () => {
    const nextErrors: MenuItemErrors = {};
    if (!draft.id.trim()) {
      nextErrors.id = 'Укажите идентификатор';
    }
    if (!draft.label.trim()) {
      nextErrors.label = 'Укажите заголовок';
    }
    if (!draft.href.trim()) {
      nextErrors.href = 'Укажите ссылку';
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      return;
    }
    onSubmit(normalizeMenuItemDraft(draft));
    onClose();
  };

  if (!open) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Редактирование пункта меню"
      size="lg"
      footer={(
        <>
          <Button variant="ghost" onClick={onClose}>
            Отмена
          </Button>
          <Button onClick={handleSubmit}>
            Сохранить
          </Button>
        </>
      )}
    >
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">ID</label>
            <Input value={draft.id} onChange={(event) => handleChange('id', event.target.value)} placeholder="menu-item" />
            <FieldError message={errors.id} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Заголовок</label>
            <Input value={draft.label} onChange={(event) => handleChange('label', event.target.value)} placeholder="Документация" />
            <FieldError message={errors.label} />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Ссылка</label>
            <Input value={draft.href} onChange={(event) => handleChange('href', event.target.value)} placeholder="/docs" />
            <FieldError message={errors.href} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Target</label>
            <Select
              value={draft.target ?? '_self'}
              onChange={(event) =>
                setDraft((prev) => ({
                  ...prev,
                  target: event.target.value === '_blank' ? '_blank' : '_self',
                }))
              }
            >
              {HEADER_LINK_TARGET_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Описание</label>
            <Textarea
              rows={2}
              value={draft.description ?? ''}
              onChange={(event) => handleChange('description', event.target.value)}
              placeholder="Короткое описание пункта"
              className="text-xs"
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Бейдж</label>
              <Input value={draft.badge ?? ''} onChange={(event) => handleChange('badge', event.target.value)} placeholder="New" />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Иконка</label>
              <Input value={draft.icon ?? ''} onChange={(event) => handleChange('icon', event.target.value)} placeholder="sparkles" />
            </div>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Analytics event</label>
          <Input
            value={draft.analytics?.event ?? ''}
            onChange={(event) => handleAnalyticsChange(event.target.value)}
            placeholder="header.link_click"
          />
        </div>

        {allowChildren ? (
          <div className="space-y-3 rounded-lg border border-gray-200 p-3 dark:border-dark-600">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">Подпункты</div>
                <div className="text-xs text-gray-500 dark:text-dark-200">
                  Отображаются в выпадающем подменю. ID и ссылка обязательны.
                </div>
              </div>
              <Button type="button" size="xs" variant="outlined" onClick={handleAddChild}>
                <Plus className="mr-1 h-3 w-3" />
                Добавить подпункт
              </Button>
            </div>

            {children.length === 0 ? (
              <div className="rounded border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-500 dark:border-dark-600 dark:bg-dark-800/40 dark:text-dark-200">
                Подпункты не заданы.
              </div>
            ) : (
              <div className="space-y-2">
                {children.map((child, index) => (
                  <div
                    key={`child-${index}-${child.id}`}
                    className="rounded-md border border-gray-200 bg-white p-3 text-xs dark:border-dark-600 dark:bg-dark-900/60"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-medium text-gray-800 dark:text-dark-100">
                        {child.label || `Подпункт ${index + 1}`}
                      </span>
                      <div className="flex items-center gap-1">
                        <Button
                          type="button"
                          size="xs"
                          variant="ghost"
                          onClick={() => handleChildReorder(index, Math.max(index - 1, 0))}
                          disabled={index === 0}
                        >
                          ↑
                        </Button>
                        <Button
                          type="button"
                          size="xs"
                          variant="ghost"
                          onClick={() => handleChildReorder(index, Math.min(index + 1, children.length - 1))}
                          disabled={index === children.length - 1}
                        >
                          ↓
                        </Button>
                        <Button
                          type="button"
                          size="xs"
                          variant="ghost"
                          className="text-rose-600 hover:text-rose-700"
                          onClick={() => handleRemoveChild(index)}
                        >
                          Удалить
                        </Button>
                      </div>
                    </div>

                    <div className="mt-2 grid gap-2 sm:grid-cols-2">
                      <Input
                        value={child.id}
                        onChange={(event) => handleChildFieldChange(index, 'id', event.target.value)}
                        placeholder="submenu-item"
                      />
                      <Input
                        value={child.label}
                        onChange={(event) => handleChildFieldChange(index, 'label', event.target.value)}
                        placeholder="Пункт"
                      />
                    </div>
                    <div className="mt-2 grid gap-2 sm:grid-cols-2">
                      <Input
                        value={child.href}
                        onChange={(event) => handleChildFieldChange(index, 'href', event.target.value)}
                        placeholder="/child"
                      />
                      <Input
                        value={child.badge ?? ''}
                        onChange={(event) => handleChildFieldChange(index, 'badge', event.target.value)}
                        placeholder="Бейдж"
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </div>
    </Dialog>
  );
}
export function SiteBlockHeaderForm({
  value,
  disabled,
  onChange,
  remoteIssues = [],
  generalMessages = [],
  validationLoading = false,
}: SiteBlockHeaderFormProps): React.ReactElement | null {
  const config = React.useMemo(() => ensureHeaderConfig(value ?? createDefaultHeaderConfig()), [value]);
  const localIssues = React.useMemo(() => validateHeaderConfig(config), [config]);
  const issues = React.useMemo(
    () => [...localIssues, ...remoteIssues],
    [localIssues, remoteIssues],
  );
  const [modalState, setModalState] = React.useState<{
    descriptor: MenuGroupDescriptor;
    index: number | null;
    initial: HeaderMenuItem;
  } | null>(null);

  const updateConfig = React.useCallback(
    (updater: (current: SiteHeaderConfig) => SiteHeaderConfig) => {
      onChange(updater(config));
    },
    [config, onChange],
  );

  const handleBrandingChange = (key: keyof SiteHeaderConfig['branding'], nextValue: unknown) => {
    updateConfig((current) => ({
      ...current,
      branding: {
        ...current.branding,
        [key]: nextValue,
      },
    }));
  };

  const handleLogoChange = (
    key: keyof NonNullable<SiteHeaderConfig['branding']['logo']>,
    nextValue: string,
  ) => {
    updateConfig((current) => ({
      ...current,
      branding: {
        ...current.branding,
        logo: {
          ...(current.branding.logo ?? createDefaultLogo()),
          [key]: nextValue,
        },
      },
    }));
  };

  const handleGroupUpdate = (groupKey: MenuGroupKey, group: HeaderMenuGroup) => {
    updateConfig((current) => setMenuGroup(current, groupKey, group));
  };

  const openModal = (descriptor: MenuGroupDescriptor, index: number | null) => {
    const items = getMenuGroup(config, descriptor.key);
    const initialItem =
      index == null
        ? {
            ...createDefaultMenuItem(),
            children: descriptor.allowChildren ? [] : null,
          }
        : cloneMenuItem(items[index]);
    setModalState({ descriptor, index, initial: initialItem });
  };

  const handleModalSubmit = (item: HeaderMenuItem) => {
    if (!modalState) {
      return;
    }
    const { descriptor, index } = modalState;
    updateConfig((current) => {
      const items = cloneMenuGroup(getMenuGroup(current, descriptor.key));
      if (index == null) {
        items.push(item);
      } else {
        items[index] = item;
      }
      return setMenuGroup(current, descriptor.key, items);
    });
    setModalState(null);
  };

  const handleModalClose = () => setModalState(null);

  const handleCtaToggle = (enabled: boolean, target: 'desktop' | 'mobile') => {
    updateConfig((current) => {
      const nextNavigation = { ...current.navigation };
      if (target === 'desktop') {
        nextNavigation.cta = enabled ? current.navigation.cta ?? createDefaultCta() : null;
      } else {
        nextNavigation.mobile = {
          menu: current.navigation.mobile?.menu ?? createDefaultMenuGroup(),
          cta: enabled ? current.navigation.mobile?.cta ?? createDefaultCta() : null,
        };
      }
      return {
        ...current,
        navigation: nextNavigation,
      };
    });
  };

  const handleCtaChange = (
    target: 'desktop' | 'mobile',
    updater: (cta: Exclude<HeaderCta, null>) => Exclude<HeaderCta, null>,
  ) => {
    updateConfig((current) => {
      if (target === 'desktop' && current.navigation.cta) {
        return {
          ...current,
          navigation: {
            ...current.navigation,
            cta: updater(current.navigation.cta),
          },
        };
      }
      if (target === 'mobile' && current.navigation.mobile?.cta) {
        return {
          ...current,
          navigation: {
            ...current.navigation,
            mobile: {
              menu: current.navigation.mobile.menu ?? createDefaultMenuGroup(),
              cta: updater(current.navigation.mobile.cta),
            },
          },
        };
      }
      return current;
    });
  };

  const handleLayoutChange = (
    key: keyof NonNullable<SiteHeaderConfig['layout']>,
    value: HeaderLayoutVariant | boolean,
  ) => {
    updateConfig((current) => ({
      ...current,
      layout: {
        variant: current.layout?.variant ?? 'default',
        sticky: current.layout?.sticky ?? true,
        hideOnScroll: current.layout?.hideOnScroll ?? false,
        [key]: value,
      },
    }));
  };

  const generalIssues = React.useMemo(() => {
    const unique = new Set<string>();
    generalMessages.forEach((message) => {
      const trimmed = typeof message === 'string' ? message.trim() : '';
      if (trimmed) {
        unique.add(trimmed);
      }
    });
    return Array.from(unique);
  }, [generalMessages]);

  return (
    <>
      {validationLoading ? (
        <div className="flex items-center gap-2 rounded-lg border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-600 dark:border-dark-600 dark:bg-dark-800/40 dark:text-dark-200">
          <Spinner className="h-4 w-4" />
          <span>Проверяем конфигурацию…</span>
        </div>
      ) : null}

      {generalIssues.length ? (
        <Card className="space-y-2 border-amber-200 bg-amber-50/70 p-4 text-xs text-amber-800 dark:border-amber-400/40 dark:bg-amber-900/20 dark:text-amber-200">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div className="space-y-1">
              {generalIssues.map((message) => (
                <div key={message}>{message}</div>
              ))}
            </div>
          </div>
        </Card>
      ) : null}

      <Section title="Брендинг">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Название</label>
            <Input
              value={config.branding.title}
              onChange={(event) => handleBrandingChange('title', event.target.value)}
              placeholder="Caves"
              disabled={disabled}
            />
            <FieldError message={hasIssue(issues, 'branding.title')?.message} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Ссылка</label>
            <Input
              value={config.branding.href}
              onChange={(event) => handleBrandingChange('href', event.target.value)}
              placeholder="/"
              disabled={disabled}
            />
            <FieldError message={hasIssue(issues, 'branding.href')?.message} />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Подзаголовок</label>
            <Input
              value={config.branding.subtitle ?? ''}
              onChange={(event) => handleBrandingChange('subtitle', event.target.value)}
              placeholder="Документация, навигация, CTA"
              disabled={disabled}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Логотип (light)</label>
            <Input
              value={config.branding.logo?.light ?? ''}
              onChange={(event) => handleLogoChange('light', event.target.value)}
              placeholder="https://cdn.dev/logo-light.svg"
              disabled={disabled}
            />
            <FieldError message={hasIssue(issues, 'branding.logo.light')?.message} />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Логотип (dark)</label>
            <Input
              value={config.branding.logo?.dark ?? ''}
              onChange={(event) => handleLogoChange('dark', event.target.value)}
              placeholder="https://cdn.dev/logo-dark.svg"
              disabled={disabled}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Alt текст</label>
            <Input
              value={config.branding.logo?.alt ?? ''}
              onChange={(event) => handleLogoChange('alt', event.target.value)}
              placeholder="Caves"
              disabled={disabled}
            />
          </div>
        </div>
      </Section>

      {MENU_GROUPS.map((descriptor) => (
        <MenuGroupEditor
          key={descriptor.key}
          descriptor={descriptor}
          items={getMenuGroup(config, descriptor.key)}
          issues={issues}
          disabled={disabled}
          onReorder={(next) => handleGroupUpdate(descriptor.key, next)}
          onEdit={(index) => openModal(descriptor, index)}
          onRemove={(index) => {
            const items = getMenuGroup(config, descriptor.key).filter((_, i) => i !== index);
            handleGroupUpdate(descriptor.key, items);
          }}
          onAdd={() => openModal(descriptor, null)}
        />
      ))}

      <Section title="CTA (desktop)">
        <div className="flex items-center justify-between gap-4 rounded-lg border border-gray-200 p-3 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200">
          <div>
            <div className="font-medium text-gray-800 dark:text-dark-100">Показ кнопки</div>
            <div>Включите, если нужна основная кнопка в хедере.</div>
          </div>
          <Switch
            checked={Boolean(config.navigation.cta)}
            onChange={(event) => handleCtaToggle(event.currentTarget.checked, 'desktop')}
            disabled={disabled}
          />
        </div>
        {config.navigation.cta ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Текст</label>
              <Input
                value={config.navigation.cta.label}
                onChange={(event) =>
                  handleCtaChange('desktop', (cta) => ({ ...cta, label: event.target.value }))
                }
                placeholder="Начать"
                disabled={disabled}
              />
              <FieldError message={hasIssue(issues, 'navigation.cta.label')?.message} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Ссылка</label>
              <Input
                value={config.navigation.cta.href}
                onChange={(event) =>
                  handleCtaChange('desktop', (cta) => ({ ...cta, href: event.target.value }))
                }
                placeholder="/signup"
                disabled={disabled}
              />
              <FieldError message={hasIssue(issues, 'navigation.cta.href')?.message} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Стиль</label>
              <Select
                value={config.navigation.cta.style ?? 'primary'}
                onChange={(event) =>
                  handleCtaChange('desktop', (cta) => ({
                    ...cta,
                    style: event.target.value as HeaderCtaStyle,
                  }))
                }
                disabled={disabled}
              >
                {HEADER_CTA_STYLE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Target</label>
              <Select
                value={config.navigation.cta.target ?? '_self'}
                onChange={(event) =>
                  handleCtaChange('desktop', (cta) => ({
                    ...cta,
                    target: event.target.value === '_blank' ? '_blank' : '_self',
                  }))
                }
                disabled={disabled}
              >
                {HEADER_LINK_TARGET_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        ) : null}
      </Section>

      <Section title="Мобильное меню">
        <div className="flex items-center justify-between gap-4 rounded-lg border border-gray-200 p-3 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200">
          <div>
            <div className="font-medium text-gray-800 dark:text-dark-100">CTA в мобильном меню</div>
            <div>Опциональная кнопка внутри бургер-меню.</div>
          </div>
          <Switch
            checked={Boolean(config.navigation.mobile?.cta)}
            onChange={(event) => handleCtaToggle(event.currentTarget.checked, 'mobile')}
            disabled={disabled}
          />
        </div>
        {config.navigation.mobile?.cta ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Текст</label>
              <Input
                value={config.navigation.mobile.cta.label}
                onChange={(event) =>
                  handleCtaChange('mobile', (cta) => ({ ...cta, label: event.target.value }))
                }
                disabled={disabled}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Ссылка</label>
              <Input
                value={config.navigation.mobile.cta.href}
                onChange={(event) =>
                  handleCtaChange('mobile', (cta) => ({ ...cta, href: event.target.value }))
                }
                disabled={disabled}
              />
            </div>
          </div>
        ) : null}
      </Section>

      <Section title="Настройки отображения">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Вариант</label>
            <Select
              value={config.layout?.variant ?? 'default'}
              onChange={(event) =>
                handleLayoutChange('variant', event.target.value as HeaderLayoutVariant)
              }
              disabled={disabled}
            >
              {HEADER_VARIANT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Закрепление</label>
            <div className="flex items-center gap-3 rounded-lg border border-gray-200 px-3 py-2 dark:border-dark-600">
              <span className="text-xs text-gray-600 dark:text-dark-200">Закреплять хедер</span>
              <Switch
                checked={config.layout?.sticky ?? true}
                onChange={(event) => handleLayoutChange('sticky', event.currentTarget.checked)}
                disabled={disabled}
              />
            </div>
          </div>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-600 dark:text-dark-200">
            Скрывать при скролле вниз
          </label>
          <div className="flex items-center gap-3 rounded-lg border border-gray-200 px-3 py-2 dark:border-dark-600">
            <span className="text-xs text-gray-600 dark:text-dark-200">
              Хедер исчезает при прокрутке вниз и возвращается при прокрутке вверх
            </span>
            <Switch
              checked={config.layout?.hideOnScroll ?? false}
              onChange={(event) => handleLayoutChange('hideOnScroll', event.currentTarget.checked)}
              disabled={disabled}
            />
          </div>
        </div>
      </Section>

      <Section
        title="Фичи"
        description="Дополнительные переключатели и параметры, используемые компонентом."
      >
        <FeaturesEditor
          features={config.features}
          disabled={disabled}
          onChange={(next) =>
            updateConfig((current) => ({
              ...current,
              features: next,
            }))
          }
        />
      </Section>

      <MenuItemModal
        open={Boolean(modalState)}
        allowChildren={modalState?.descriptor.allowChildren ?? false}
        initial={modalState?.initial ?? createDefaultMenuItem()}
        onSubmit={handleModalSubmit}
        onClose={handleModalClose}
      />
    </>
  );
}

export default SiteBlockHeaderForm;

type FeaturesEditorProps = {
  features: Record<string, string | number | boolean | null> | undefined;
  disabled?: boolean;
  onChange: (next: Record<string, string | number | boolean | null>) => void;
};

function FeaturesEditor({ features, disabled, onChange }: FeaturesEditorProps): React.ReactElement {
  const entries = Object.entries(features ?? {});
  const [newKey, setNewKey] = React.useState('');

  const handleUpdate = (key: string, value: string | number | boolean | null) => {
    onChange({
      ...(features ?? {}),
      [key]: value,
    });
  };

  const handleRemove = (key: string) => {
    const next = { ...(features ?? {}) };
    delete next[key];
    onChange(next);
  };

  const handleAdd = () => {
    const trimmed = newKey.trim();
    if (!trimmed || (features && trimmed in features)) {
      return;
    }
    onChange({
      ...(features ?? {}),
      [trimmed]: true,
    });
    setNewKey('');
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          value={newKey}
          onChange={(event) => setNewKey(event.target.value)}
          placeholder="feature_name"
          disabled={disabled}
          className="w-48"
        />
        <Button type="button" onClick={handleAdd} disabled={disabled || !newKey.trim()}>
          Добавить фичу
        </Button>
      </div>
      {entries.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-500 dark:border-dark-600 dark:bg-dark-800/40 dark:text-dark-200">
          Фичи пока не настроены.
        </div>
      ) : (
        <div className="space-y-3">
          {entries.map(([key, value]) => {
            const valueType = typeof value;
            const isBoolean = valueType === 'boolean';
            const isNumber = valueType === 'number';
            return (
              <Card
                key={key}
                className="flex flex-wrap items-center gap-3 border border-gray-200 p-3 text-xs dark:border-dark-600"
              >
                <div className="flex-1 space-y-1">
                  <div className="font-medium text-gray-700 dark:text-dark-100">{key}</div>
                  <div className="flex flex-wrap items-center gap-3">
                    <Select
                      value={isBoolean ? 'boolean' : isNumber ? 'number' : 'string'}
                      onChange={(event) => {
                        const nextType = event.target.value;
                        if (nextType === 'boolean') {
                          handleUpdate(key, Boolean(value));
                        } else if (nextType === 'number') {
                          const numeric = Number(value);
                          handleUpdate(key, Number.isNaN(numeric) ? 0 : numeric);
                        } else {
                          handleUpdate(key, String(value ?? ''));
                        }
                      }}
                      disabled={disabled}
                      className="w-32"
                    >
                      <option value="boolean">Boolean</option>
                      <option value="number">Number</option>
                      <option value="string">String</option>
                    </Select>
                    {isBoolean ? (
                      <Switch
                        checked={Boolean(value)}
                        onChange={(event) => handleUpdate(key, event.currentTarget.checked)}
                        disabled={disabled}
                      />
                    ) : (
                      <Input
                        value={
                          value === null
                            ? ''
                            : typeof value === 'number'
                            ? String(value)
                            : (value as string)
                        }
                        onChange={(event) => {
                          if (isNumber) {
                            handleUpdate(key, Number(event.target.value) || 0);
                          } else {
                            handleUpdate(key, event.target.value);
                          }
                        }}
                        disabled={disabled}
                        placeholder={isNumber ? '0' : 'value'}
                        className="min-w-[160px]"
                      />
                    )}
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  onClick={() => handleRemove(key)}
                  disabled={disabled}
                >
                  Удалить
                </Button>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
