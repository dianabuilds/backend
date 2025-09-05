import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import SendToUserModal from "../components/notifications/SendToUserModal";
import BroadcastForm from "../components/notifications/BroadcastForm";
import CampaignTable from "../components/notifications/CampaignTable";
import UserNotifications from "../components/notifications/UserNotifications";

export default function Notifications() {
  const [sendOpen, setSendOpen] = useState(false);
  const [broadcastOpen, setBroadcastOpen] = useState(false);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Notifications</h1>
      <Tabs defaultValue="campaigns">
        <TabsList className="mb-4">
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="user">My notifications</TabsTrigger>
        </TabsList>
        <TabsContent value="campaigns">
          <div className="mb-4">
            <button
              className="px-3 py-1 rounded bg-blue-600 text-white"
              onClick={() => setBroadcastOpen(true)}
            >
              Start broadcast
            </button>
          </div>
          <CampaignTable />
        </TabsContent>
        <TabsContent value="user">
          <div className="mb-4">
            <button
              className="px-3 py-1 rounded bg-blue-600 text-white"
              onClick={() => setSendOpen(true)}
            >
              Send notification
            </button>
          </div>
          <UserNotifications />
        </TabsContent>
      </Tabs>
      <SendToUserModal isOpen={sendOpen} onClose={() => setSendOpen(false)} />
      <BroadcastForm isOpen={broadcastOpen} onClose={() => setBroadcastOpen(false)} />
    </div>
  );
}
