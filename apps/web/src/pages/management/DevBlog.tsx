import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Spinner } from '@ui';
import { DEV_BLOG_TAG } from '@shared/types/nodes';
import { ContentNodesList } from '../../features/content/nodes';

export default function ManagementDevBlogPage(): React.ReactElement {
  const navigate = useNavigate();
  const location = useLocation();

  const isPinnedToDevBlog = React.useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get('tag') === DEV_BLOG_TAG;
  }, [location.search]);

  React.useEffect(() => {
    if (isPinnedToDevBlog) {
      return;
    }
    const params = new URLSearchParams(location.search);
    params.set('tag', DEV_BLOG_TAG);
    const query = params.toString();
    navigate({ pathname: location.pathname, search: query ? `?${query}` : '' }, { replace: true });
  }, [isPinnedToDevBlog, location.pathname, location.search, navigate]);

  if (!isPinnedToDevBlog) {
    return (
      <div className="flex h-full items-center justify-center py-20">
        <Spinner />
      </div>
    );
  }

  return <ContentNodesList />;
}
