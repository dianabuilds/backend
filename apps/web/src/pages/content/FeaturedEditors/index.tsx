// Import Dependencies
import { CSSProperties } from 'react';

// Local Imports

type Editor = {
  uid: string;
  name: string;
  avatar?: string;
  posts: string;
  views: string;
  followers: string;
};

const editors: Editor[] = [
  { uid: '1', name: 'Иван Петров', avatar: '/images/avatar/avatar-5.jpg', posts: '2348', views: '3.45k', followers: '78' },
  { uid: '2', name: 'Ольга Смирнова', avatar: '/images/avatar/avatar-18.jpg', posts: '2.34k', views: '93.3k', followers: '566' },
  { uid: '3', name: 'Максим Фёдоров', avatar: '/images/avatar/avatar-6.jpg', posts: '361', views: '37.2k', followers: '823' },
  { uid: '4', name: 'Анна Морозова', avatar: '/images/avatar/avatar-11.jpg', posts: '18', views: '364.4k', followers: '54.2k' },
];

function EditorCard(e: Editor) {
  return (
    <div className="min-w-[240px] shrink-0 rounded-lg border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-800">
      <div className="flex items-center gap-3">
        <div className="size-10 overflow-hidden rounded-full bg-gray-100">
          {e.avatar ? <img src={e.avatar} alt={e.name} className="h-full w-full object-cover" /> : <div className="flex h-full w-full items-center justify-center text-sm font-semibold">{e.name.slice(0,2)}</div>}
        </div>
        <div className="min-w-0">
          <div className="truncate font-medium text-gray-800 dark:text-dark-100">{e.name}</div>
          <div className="text-xs text-gray-400 dark:text-dark-300">Редактор</div>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-sm font-medium text-gray-800 dark:text-dark-100">{e.posts}</div>
          <div className="text-xs text-gray-400">Посты</div>
        </div>
        <div>
          <div className="text-sm font-medium text-gray-800 dark:text-dark-100">{e.views}</div>
          <div className="text-xs text-gray-400">Просмотры</div>
        </div>
        <div>
          <div className="text-sm font-medium text-gray-800 dark:text-dark-100">{e.followers}</div>
          <div className="text-xs text-gray-400">Подписчики</div>
        </div>
      </div>
    </div>
  );
}

export function FeaturedEditors() {
  return (
    <div className="transition-content mt-4 pl-(--margin-x) sm:mt-5 lg:mt-6">
      <div className="rounded-l-lg bg-info/10 pb-1 pt-4 dark:bg-dark-800">
        <h2 className="truncate px-4 text-base font-medium tracking-wide text-gray-800 dark:text-dark-100 sm:px-5">Редакторы</h2>
        <div
          className="custom-scrollbar mt-4 flex space-x-4 overflow-x-auto px-4 pb-4 sm:px-5"
          style={{ '--margin-scroll': '1.25rem' } as CSSProperties}
        >
          {editors.map((editor) => (
            <EditorCard key={editor.uid} {...editor} />
          ))}
        </div>
      </div>
    </div>
  );
}
