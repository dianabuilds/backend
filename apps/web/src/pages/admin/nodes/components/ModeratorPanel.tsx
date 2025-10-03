import React from 'react';



import { Badge, Button, Card, Switch, useToast } from '@ui';







import { useConfirmDialog } from '../../../../shared/hooks/useConfirmDialog';



import { extractErrorMessage } from '../../../../shared/utils/errors';



import { disableAdminComments, lockAdminComments } from '../api';



import type { AdminNodeEngagementCommentSummary, AdminNodeEngagementSummary } from '../types';







type ModeratorPanelProps = {



  nodeId: string;



  summary: AdminNodeEngagementSummary | null;



  refreshing?: boolean;



  onRefresh?: () => Promise<void> | void;



};







export function ModeratorPanel({ nodeId, summary, refreshing, onRefresh }: ModeratorPanelProps) {



  const { pushToast } = useToast();



  const { confirm, confirmationElement } = useConfirmDialog();



  const [lockBusy, setLockBusy] = React.useState(false);



  const [disableBusy, setDisableBusy] = React.useState(false);



  const commentMeta: AdminNodeEngagementCommentSummary | null = summary?.comments ?? null;



  const locked = Boolean(commentMeta?.locked);



  const disabled = Boolean(commentMeta?.disabled);







  const handleRefresh = React.useCallback(async () => {



    if (!onRefresh) return;



    await onRefresh();



  }, [onRefresh]);







  const handleToggleLock = React.useCallback(



    async (next: boolean) => {



      const proceed = next



        ? await confirm({



            title: 'Lock comments?',



            description: 'Readers will not be able to add new comments until the lock is lifted.',



            confirmLabel: 'Lock comments',



            cancelLabel: 'Cancel',



          })



        : true;



      if (!proceed) return;



      setLockBusy(true);



      try {



        await lockAdminComments(nodeId, { locked: next, reason: next ? 'Locked via admin UI' : undefined });



        pushToast({ intent: 'success', description: next ? 'Comments locked for this node.' : 'Comments unlocked.' });



        await handleRefresh();



      } catch (err) {



        pushToast({ intent: 'error', description: extractErrorMessage(err) });



      } finally {



        setLockBusy(false);



      }



    },



    [confirm, handleRefresh, nodeId, pushToast],



  );







  const handleToggleDisable = React.useCallback(



    async (next: boolean) => {



      const proceed = await confirm({



        title: next ? 'Disable comments?' : 'Enable comments?',



        description: next



          ? 'Existing comments remain visible, but new messages will be blocked.'



          : 'Readers will be able to add new comments again.',



        confirmLabel: next ? 'Disable' : 'Enable',



        cancelLabel: 'Cancel',



        destructive: next,



      });



      if (!proceed) return;



      setDisableBusy(true);



      try {



        await disableAdminComments(nodeId, { disabled: next, reason: next ? 'Disabled via admin UI' : undefined });



        pushToast({ intent: 'success', description: next ? 'Comments disabled.' : 'Comments enabled.' });



        await handleRefresh();



      } catch (err) {



        pushToast({ intent: 'error', description: extractErrorMessage(err) });



      } finally {



        setDisableBusy(false);



      }



    },



    [confirm, handleRefresh, nodeId, pushToast],



  );







  return (



    <>



      <Card className="space-y-5 p-6">



        <div className="space-y-1">



          <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Moderator panel</h3>



          <p className="text-sm text-neutral-600 dark:text-neutral-300">



            Control comment availability and inspect moderation context.



          </p>



        </div>







        <div className="space-y-4 text-sm text-neutral-700 dark:text-neutral-200">



          <div className="flex items-center justify-between gap-3">



            <div>



              <div className="font-medium text-neutral-900 dark:text-neutral-100">Lock comments</div>



              <div className="text-xs text-neutral-500 dark:text-neutral-400">



                Prevents new comments while moderators investigate.



              </div>



            </div>



            <Switch



              checked={locked}



              disabled={lockBusy}



              data-testid="moderator-lock-toggle"



              data-analytics="admin.comments.lock"



              onChange={(event) => handleToggleLock(event.currentTarget.checked)}



            />



          </div>



          <div className="flex items-center justify-between gap-3">



            <div>



              <div className="font-medium text-neutral-900 dark:text-neutral-100">Disable comments</div>



              <div className="text-xs text-neutral-500 dark:text-neutral-400">



                Hides the reply form entirely for this node.



              </div>



            </div>



            <Switch



              checked={disabled}



              disabled={disableBusy}



              data-testid="moderator-disable-toggle"



              data-analytics="admin.comments.disable"



              onChange={(event) => handleToggleDisable(event.currentTarget.checked)}



            />



          </div>



        </div>







        <div className="space-y-2 text-sm text-neutral-600 dark:text-neutral-300">



          <div className="flex items-center gap-2">



            <span className="font-medium text-neutral-800 dark:text-neutral-200">Locked by:</span>



            <span>{commentMeta?.locked_by ?? 'N/A'}</span>



          </div>



          <div className="flex items-center gap-2">



            <span className="font-medium text-neutral-800 dark:text-neutral-200">Locked at:</span>



            <span>{commentMeta?.locked_at ?? 'N/A'}</span>



          </div>



          <div className="flex items-center gap-2">



            <span className="font-medium text-neutral-800 dark:text-neutral-200">Bans in effect:</span>



            <Badge color={commentMeta?.bans_count ? 'warning' : 'neutral'} variant="soft">



              {commentMeta?.bans_count ?? 0}



            </Badge>



          </div>



          <div className="flex items-center gap-2">



            <span className="font-medium text-neutral-800 dark:text-neutral-200">Last comment:</span>



            <span>{commentMeta?.last_comment_created_at ?? 'N/A'}</span>



          </div>



        </div>







        <div className="flex items-center gap-2">



          <Button size="sm" variant="outlined" color="neutral" onClick={handleRefresh} disabled={refreshing} data-testid="moderator-refresh" data-analytics="admin.comments.refresh.summary">



            {refreshing ? 'Refreshing...' : 'Refresh summary'}



          </Button>



        </div>



      </Card>







      {confirmationElement}



    </>



  );



}







