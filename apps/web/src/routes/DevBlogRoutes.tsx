import React from 'react';
import { Route, Routes } from 'react-router-dom';
import DevBlogListPage from '../pages/public/DevBlogListPage';
import DevBlogPostPage from '../pages/public/DevBlogPostPage';

export default function DevBlogRoutes(): React.ReactElement {
  return (
    <Routes>
      <Route index element={<DevBlogListPage />} />
      <Route path=":slug" element={<DevBlogPostPage />} />
    </Routes>
  );
}
