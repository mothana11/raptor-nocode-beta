import React, { useState } from 'react';
import axios from 'axios';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (user: any, token: string) => void;
  isMandatory?: boolean; // New prop to make modal mandatory
}

interface OnboardingData {
  travel_preferences: {
    seat_preference?: string;
    meal_preference?: string;
    accommodation_type?: string;
    price_range?: string;
    travel_style?: string;
    notification_preference?: string;
  };
  travel_style: string;
  budget_range: string;
  frequent_destinations: string[];
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onAuthSuccess, isMandatory = false }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Login/Register form data
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    nationality: ''
  });
  
  // Onboarding form data
  const [onboardingData, setOnboardingData] = useState<OnboardingData>({
    travel_preferences: {},
    travel_style: '',
    budget_range: '',
    frequent_destinations: []
  });

  if (!isOpen) return null;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleOnboardingChange = (section: string, key: string, value: string) => {
    if (section === 'preferences') {
      setOnboardingData({
        ...onboardingData,
        travel_preferences: {
          ...onboardingData.travel_preferences,
          [key]: value
        }
      });
    } else {
      setOnboardingData({
        ...onboardingData,
        [key]: value
      });
    }
  };

  const handleDestinationAdd = (destination: string) => {
    if (destination && !onboardingData.frequent_destinations.includes(destination)) {
      setOnboardingData({
        ...onboardingData,
        frequent_destinations: [...onboardingData.frequent_destinations, destination]
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const response = await axios.post(`http://localhost:8000${endpoint}`, formData);
      
      if (response.data.access_token) {
        localStorage.setItem('auth_token', response.data.access_token);
        localStorage.setItem('user_data', JSON.stringify(response.data.user));
        
        if (!isLogin) {
          // Show onboarding for new users
          setShowOnboarding(true);
        } else {
          onAuthSuccess(response.data.user, response.data.access_token);
          onClose();
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleOnboardingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem('auth_token');
      await axios.post('http://localhost:8000/auth/onboarding', onboardingData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
      onAuthSuccess(userData, token!);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Onboarding failed');
    } finally {
      setLoading(false);
    }
  };

  const renderAuthForm = () => (
    <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-auto">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            {isMandatory 
              ? '🔐 Login Required to Continue' 
              : (isLogin ? 'Welcome Back!' : 'Create Account')
            }
          </h2>
          {!isMandatory && (
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {isMandatory && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-700">
              🎯 Please create an account or sign in to access your personalized AI travel assistant. Your account enables us to learn your preferences and provide better recommendations over time.
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <input
                  type="text"
                  name="first_name"
                  placeholder="First Name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="text"
                  name="last_name"
                  placeholder="Last Name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <input
                type="text"
                name="nationality"
                placeholder="Nationality (optional)"
                value={formData.nationality}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </>
          )}
          
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleInputChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );

  const renderOnboarding = () => (
    <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-auto">
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Welcome! Let's personalize your experience</h2>
        
        <form onSubmit={handleOnboardingSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Travel Style</label>
            <select
              value={onboardingData.travel_style}
              onChange={(e) => handleOnboardingChange('', 'travel_style', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select your travel style</option>
              <option value="business">Business</option>
              <option value="leisure">Leisure</option>
              <option value="adventure">Adventure</option>
              <option value="cultural">Cultural</option>
              <option value="relaxation">Relaxation</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Budget Range</label>
            <select
              value={onboardingData.budget_range}
              onChange={(e) => handleOnboardingChange('', 'budget_range', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select your budget range</option>
              <option value="budget">Budget ($50-150/day)</option>
              <option value="mid-range">Mid-range ($150-300/day)</option>
              <option value="luxury">Luxury ($300+/day)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Seat Preference</label>
              <select
                value={onboardingData.travel_preferences.seat_preference || ''}
                onChange={(e) => handleOnboardingChange('preferences', 'seat_preference', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No preference</option>
                <option value="aisle">Aisle</option>
                <option value="window">Window</option>
                <option value="middle">Middle</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Meal Preference</label>
              <select
                value={onboardingData.travel_preferences.meal_preference || ''}
                onChange={(e) => handleOnboardingChange('preferences', 'meal_preference', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No preference</option>
                <option value="vegetarian">Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="kosher">Kosher</option>
                <option value="halal">Halal</option>
                <option value="gluten-free">Gluten-free</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Accommodation Preference</label>
            <select
              value={onboardingData.travel_preferences.accommodation_type || ''}
              onChange={(e) => handleOnboardingChange('preferences', 'accommodation_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">No preference</option>
              <option value="hotel">Hotel</option>
              <option value="resort">Resort</option>
              <option value="apartment">Apartment</option>
              <option value="hostel">Hostel</option>
              <option value="boutique">Boutique</option>
            </select>
          </div>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
              {error}
            </div>
          )}

          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => {
                // Skip onboarding
                const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
                const token = localStorage.getItem('auth_token');
                onAuthSuccess(userData, token!);
                onClose();
              }}
              className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400"
            >
              Skip for now
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Complete Setup'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={isMandatory ? undefined : onClose}
    >
      <div onClick={(e) => e.stopPropagation()}>
        {showOnboarding ? renderOnboarding() : renderAuthForm()}
      </div>
    </div>
  );
};

export default AuthModal; 