/**
 * PHASE 3.3 - Modal Social Principal
 * Interface principale pour les fonctionnalités sociales
 */
import React, { useState, useEffect } from 'react';
import socialService from '../../services/socialService';
import SocialFeed from './SocialFeed';
import UserProfile from './UserProfile';

const SocialModal = ({ isOpen, onClose, currentUser }) => {
  const [activeTab, setActiveTab] = useState('feed');
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [socialStats, setSocialStats] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [profileForm, setProfileForm] = useState({
    display_name: '',
    bio: '',
    location: '',
    website: '',
    privacy_level: 'public',
    show_reading_stats: true,
    show_current_reading: true,
    show_wishlist: true
  });
  const [selectedUserId, setSelectedUserId] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadInitialData();
    }
  }, [isOpen]);

  const loadInitialData = async () => {
    try {
      // Charger les notifications
      const notifResponse = await socialService.getNotifications(10);
      setNotifications(notifResponse.notifications || []);
      const unread = notifResponse.notifications?.filter(n => !n.is_read).length || 0;
      setUnreadCount(unread);

      // Charger les stats sociales
      const statsResponse = await socialService.getSocialStats();
      setSocialStats(statsResponse);

      // Charger le profil actuel
      if (currentUser?.id) {
        try {
          const profileResponse = await socialService.getProfile(currentUser.id);
          setProfileData(profileResponse);
          setProfileForm({
            display_name: profileResponse.display_name || '',
            bio: profileResponse.bio || '',
            location: profileResponse.location || '',
            website: profileResponse.website || '',
            privacy_level: profileResponse.privacy_level || 'public',
            show_reading_stats: profileResponse.show_reading_stats !== false,
            show_current_reading: profileResponse.show_current_reading !== false,
            show_wishlist: profileResponse.show_wishlist !== false
          });
        } catch (err) {
          // Profil n'existe pas encore, utiliser les valeurs par défaut
          console.log('Profil non trouvé, utilisation des valeurs par défaut');
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données sociales:', error);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      if (profileData) {
        await socialService.updateProfile(profileForm);
      } else {
        await socialService.createProfile(profileForm);
      }
      
      // Recharger le profil
      const updatedProfile = await socialService.getProfile(currentUser.id);
      setProfileData(updatedProfile);
      
      alert('Profil mis à jour avec succès !');
    } catch (error) {
      console.error('Erreur lors de la mise à jour du profil:', error);
      alert('Erreur lors de la mise à jour du profil');
    }
  };

  const handleNotificationClick = async (notification) => {
    try {
      if (!notification.is_read) {
        await socialService.markNotificationRead(notification.id);
        setNotifications(prev => 
          prev.map(n => 
            n.id === notification.id 
              ? { ...n, is_read: true }
              : n
          )
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
      
      // Traiter les actions selon le type de notification
      if (notification.type === 'new_follower' && notification.data.follower_id) {
        setSelectedUserId(notification.data.follower_id);
      }
    } catch (error) {
      console.error('Erreur lors du traitement de la notification:', error);
    }
  };

  const TabButton = ({ tabId, children, notificationCount = 0 }) => (
    <button
      onClick={() => setActiveTab(tabId)}
      className={`relative px-4 py-2 rounded-lg font-medium transition-colors ${
        activeTab === tabId
          ? 'bg-blue-500 text-white'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {children}
      {notificationCount > 0 && (
        <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
          {notificationCount}
        </span>
      )}
    </button>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Social</h2>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>

        {/* Navigation */}
        <div className="border-b border-gray-200 p-4">
          <div className="flex space-x-2">
            <TabButton tabId="feed">Feed</TabButton>
            <TabButton tabId="profile">Mon Profil</TabButton>
            <TabButton tabId="notifications" notificationCount={unreadCount}>
              Notifications
            </TabButton>
            <TabButton tabId="discover">Découvrir</TabButton>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 180px)' }}>
          
          {/* Feed Tab */}
          {activeTab === 'feed' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Votre Feed Social</h3>
              <SocialFeed />
            </div>
          )}

          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Mon Profil Social</h3>
              
              {/* Statistiques rapides */}
              {socialStats && (
                <div className="grid grid-cols-4 gap-4 mb-6">
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600">{socialStats.followers_count}</div>
                    <div className="text-sm text-gray-500">Followers</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-green-600">{socialStats.following_count}</div>
                    <div className="text-sm text-gray-500">Following</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-purple-600">{socialStats.activities_count}</div>
                    <div className="text-sm text-gray-500">Activités</div>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-orange-600">{socialStats.likes_received}</div>
                    <div className="text-sm text-gray-500">Likes</div>
                  </div>
                </div>
              )}

              {/* Formulaire de profil */}
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom d'affichage
                  </label>
                  <input
                    type="text"
                    value={profileForm.display_name}
                    onChange={(e) => setProfileForm({ ...profileForm, display_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Votre nom d'affichage"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Biographie
                  </label>
                  <textarea
                    value={profileForm.bio}
                    onChange={(e) => setProfileForm({ ...profileForm, bio: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Parlez-nous de vous..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Localisation
                    </label>
                    <input
                      type="text"
                      value={profileForm.location}
                      onChange={(e) => setProfileForm({ ...profileForm, location: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Votre ville"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Site web
                    </label>
                    <input
                      type="url"
                      value={profileForm.website}
                      onChange={(e) => setProfileForm({ ...profileForm, website: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="https://votre-site.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Niveau de confidentialité
                  </label>
                  <select
                    value={profileForm.privacy_level}
                    onChange={(e) => setProfileForm({ ...profileForm, privacy_level: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="public">Public</option>
                    <option value="friends">Amis seulement</option>
                    <option value="private">Privé</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Visibilité des données
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={profileForm.show_reading_stats}
                        onChange={(e) => setProfileForm({ ...profileForm, show_reading_stats: e.target.checked })}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">Afficher les statistiques de lecture</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={profileForm.show_current_reading}
                        onChange={(e) => setProfileForm({ ...profileForm, show_current_reading: e.target.checked })}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">Afficher les lectures en cours</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={profileForm.show_wishlist}
                        onChange={(e) => setProfileForm({ ...profileForm, show_wishlist: e.target.checked })}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">Afficher la wishlist</span>
                    </label>
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Mettre à jour le profil
                </button>
              </form>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Notifications</h3>
              
              {notifications.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-4xl mb-4">🔔</div>
                  <p className="text-gray-500">Aucune notification</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      onClick={() => handleNotificationClick(notification)}
                      className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                        notification.is_read 
                          ? 'bg-gray-50 border-gray-200' 
                          : 'bg-blue-50 border-blue-200'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          {!notification.is_read && (
                            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                          )}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{notification.title}</h4>
                          <p className="text-sm text-gray-600">{notification.message}</p>
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(notification.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Discover Tab */}
          {activeTab === 'discover' && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Découvrir des utilisateurs</h3>
              <div className="text-center py-8">
                <div className="text-gray-400 text-4xl mb-4">🔍</div>
                <p className="text-gray-500">Fonctionnalité à venir</p>
                <p className="text-sm text-gray-400 mt-2">
                  Bientôt, vous pourrez découvrir d'autres lecteurs avec des goûts similaires !
                </p>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* Modal UserProfile */}
      {selectedUserId && (
        <UserProfile
          userId={selectedUserId}
          onClose={() => setSelectedUserId(null)}
        />
      )}
    </div>
  );
};

export default SocialModal;