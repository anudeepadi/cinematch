import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Calendar, Settings, Users, LogOut, ChevronRight, Bell, Shield, Palette, Trash2 } from 'lucide-react';
import { Layout } from '../components/layout/Layout';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { useAuthStore } from '../store/authStore';
import { companionsApi } from '../api/companions';
import { moviesApi } from '../api/movies';
import { usersApi } from '../api/users';
import { Companion, Genre } from '../types';
import toast from 'react-hot-toast';

export function ProfilePage() {
  const { user, logout, updateUser } = useAuthStore();
  const [companions, setCompanions] = useState<Companion[]>([]);
  const [pendingRequests, setPendingRequests] = useState<Companion[]>([]);
  const [genres, setGenres] = useState<Genre[]>([]);
  const [showCompanionModal, setShowCompanionModal] = useState(false);
  const [companionEmail, setCompanionEmail] = useState('');
  const [nickname, setNickname] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState<'profile' | 'preferences' | 'companions'>('profile');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [comps, pending, genreList] = await Promise.all([
        companionsApi.getCompanions(),
        companionsApi.getPendingRequests(),
        moviesApi.getGenres(),
      ]);
      setCompanions(comps.filter(c => c.status === 'accepted'));
      setPendingRequests(pending);
      setGenres(genreList);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleSendRequest = async () => {
    if (!companionEmail) return;
    setLoading(true);
    try {
      await companionsApi.sendRequest(companionEmail, nickname || undefined);
      toast.success('Request sent!');
      setShowCompanionModal(false);
      setCompanionEmail('');
      setNickname('');
      loadData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to send request');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptRequest = async (linkId: number) => {
    try {
      await companionsApi.acceptRequest(linkId);
      toast.success('Request accepted!');
      loadData();
    } catch (error) {
      toast.error('Failed to accept request');
    }
  };

  const handleRejectRequest = async (linkId: number) => {
    try {
      await companionsApi.rejectRequest(linkId);
      toast.success('Request rejected');
      loadData();
    } catch (error) {
      toast.error('Failed to reject request');
    }
  };

  const handleRemoveCompanion = async (linkId: number) => {
    try {
      await companionsApi.removeCompanion(linkId);
      toast.success('Companion removed');
      loadData();
    } catch (error) {
      toast.error('Failed to remove companion');
    }
  };

  const handleUpdatePreferences = async (genreIds: number[]) => {
    try {
      await usersApi.updatePreferences({ preferred_genres: genreIds });
      updateUser({ preferred_genres: genreIds });
      toast.success('Preferences updated!');
    } catch (error) {
      toast.error('Failed to update preferences');
    }
  };

  const menuItems = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'preferences', label: 'Preferences', icon: Settings },
    { id: 'companions', label: 'Companions', icon: Users },
  ];

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
            <p className="text-zinc-400">Manage your account and preferences</p>
          </div>

          <div className="flex flex-col md:flex-row gap-8">
            {/* Sidebar */}
            <div className="md:w-64 flex-shrink-0">
              <nav className="space-y-1">
                {menuItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveSection(item.id as any)}
                    className={`
                      w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all
                      ${activeSection === item.id
                        ? 'bg-amber-500/10 text-amber-400'
                        : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white'}
                    `}
                  >
                    <item.icon size={20} />
                    {item.label}
                  </button>
                ))}
              </nav>

              <div className="mt-8 pt-8 border-t border-zinc-800">
                <button
                  onClick={() => logout()}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-all"
                >
                  <LogOut size={20} />
                  Sign out
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1">
              {/* Profile Section */}
              {activeSection === 'profile' && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
                    <div className="flex items-center gap-6 mb-6">
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-3xl font-bold text-white">
                        {user?.username?.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h2 className="text-xl font-semibold text-white">{user?.username}</h2>
                        <p className="text-zinc-400">{user?.email}</p>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center gap-3 text-zinc-400">
                        <Mail size={18} />
                        <span>{user?.email}</span>
                      </div>
                      <div className="flex items-center gap-3 text-zinc-400">
                        <Calendar size={18} />
                        <span>Joined {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Recently'}</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Preferences Section */}
              {activeSection === 'preferences' && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
                    <h3 className="text-lg font-semibold text-white mb-4">Favorite Genres</h3>
                    <div className="flex flex-wrap gap-2">
                      {genres.map((genre) => (
                        <button
                          key={genre.id}
                          onClick={() => {
                            const current = user?.preferred_genres || [];
                            const newGenres = current.includes(genre.tmdb_id)
                              ? current.filter(id => id !== genre.tmdb_id)
                              : [...current, genre.tmdb_id];
                            handleUpdatePreferences(newGenres);
                          }}
                          className={`
                            px-4 py-2 rounded-lg text-sm transition-all
                            ${user?.preferred_genres?.includes(genre.tmdb_id)
                              ? 'bg-amber-500 text-white'
                              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}
                          `}
                        >
                          {genre.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
                    <h3 className="text-lg font-semibold text-white mb-4">Year Preferences</h3>
                    <div className="flex items-center gap-4">
                      <span className="text-zinc-400">From</span>
                      <span className="text-white font-medium">{user?.year_range_min || 1970}</span>
                      <span className="text-zinc-400">to</span>
                      <span className="text-white font-medium">{user?.year_range_max || 2025}</span>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Companions Section */}
              {activeSection === 'companions' && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-6"
                >
                  {/* Pending Requests */}
                  {pendingRequests.length > 0 && (
                    <div className="p-6 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                      <h3 className="text-lg font-semibold text-amber-400 mb-4">Pending Requests</h3>
                      <div className="space-y-3">
                        {pendingRequests.map((request) => (
                          <div key={request.id} className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                                ?
                              </div>
                              <span className="text-white">New request</span>
                            </div>
                            <div className="flex gap-2">
                              <Button size="sm" onClick={() => handleAcceptRequest(request.id)}>
                                Accept
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleRejectRequest(request.id)}>
                                Decline
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Linked Companions */}
                  <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Linked Companions</h3>
                      <Button size="sm" onClick={() => setShowCompanionModal(true)}>
                        Add Companion
                      </Button>
                    </div>

                    {companions.length === 0 ? (
                      <div className="text-center py-8">
                        <Users size={40} className="text-zinc-700 mx-auto mb-3" />
                        <p className="text-zinc-500">No companions linked yet</p>
                        <p className="text-zinc-600 text-sm">Link a friend to get joint movie recommendations</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {companions.map((companion) => (
                          <div key={companion.id} className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-semibold">
                                {companion.nickname?.charAt(0) || companion.companion_user?.username?.charAt(0) || '?'}
                              </div>
                              <div>
                                <p className="text-white font-medium">
                                  {companion.nickname || companion.companion_user?.username}
                                </p>
                                <p className="text-zinc-500 text-sm">
                                  {companion.companion_user?.email}
                                </p>
                              </div>
                            </div>
                            <button
                              onClick={() => handleRemoveCompanion(companion.id)}
                              className="p-2 text-zinc-500 hover:text-red-400 transition-colors"
                            >
                              <Trash2 size={18} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </div>
          </div>

          {/* Add Companion Modal */}
          <Modal
            isOpen={showCompanionModal}
            onClose={() => setShowCompanionModal(false)}
            title="Add Companion"
          >
            <div className="space-y-4">
              <p className="text-zinc-400">
                Enter your companion's email to send them a link request.
                Once accepted, you can get joint movie recommendations!
              </p>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Email</label>
                <input
                  type="email"
                  value={companionEmail}
                  onChange={(e) => setCompanionEmail(e.target.value)}
                  placeholder="friend@example.com"
                  className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Nickname (optional)</label>
                <input
                  type="text"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="Movie Buddy"
                  className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500/50"
                />
              </div>

              <Button
                className="w-full"
                onClick={handleSendRequest}
                isLoading={loading}
                disabled={!companionEmail}
              >
                Send Request
              </Button>
            </div>
          </Modal>
        </div>
      </div>
    </Layout>
  );
}
