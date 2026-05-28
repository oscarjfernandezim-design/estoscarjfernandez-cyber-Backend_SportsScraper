// ========================================
// AUTHENTICATION MODULE
// ========================================

// API base: when page is opened from file:// use local server
window.API_BASE = window.API_BASE || ((location.protocol === 'file:') ? 'http://127.0.0.1:3000' : '');

function normalizeUser(rawUser) {
  if (!rawUser) return null;
  const email = rawUser.email || '';
  const name = rawUser.name || rawUser.full_name || 'Usuario';
  const id = rawUser.id || ('user_' + Date.now());
  const createdAt = rawUser.createdAt || rawUser.created_at || new Date().toISOString();
  const avatar = rawUser.avatar || `https://i.pravatar.cc/?img=${Math.floor(Math.random() * 70)}`;

  return {
    ...rawUser,
    id,
    email,
    name,
    full_name: rawUser.full_name || name,
    createdAt,
    avatar,
  };
}

// Simple hash function (not secure - for demo only)
function hashPassword(password) {
  let hash = 0;
  for (let i = 0; i < password.length; i++) {
    const char = password.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return 'hash_' + Math.abs(hash);
}

// ========================================
// USER MANAGEMENT
// ========================================

async function registerUser(email, password, name) {
  email = (email || '').trim().toLowerCase();
  // Validate inputs
  if (!email || !password || !name) {
    return { success: false, error: 'Todos los campos son requeridos' };
  }

  if (password.length < 6) {
    return { success: false, error: 'La contraseña debe tener al menos 6 caracteres' };
  }

  // Check if user already exists
  const users = JSON.parse(localStorage.getItem('sportsscraper_users')) || [];
  if (users.find(u => u.email === email)) {
    return { success: false, error: 'Este email ya está registrado' };
  }

  // Try backend registration first
  try {
    const response = await fetch(`${window.API_BASE}/api/auth/register`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: name, email: email, password: password })
    });

    if (response.ok) {
      const user = normalizeUser(await response.json());
      const shadowUsers = JSON.parse(localStorage.getItem('sportsscraper_users')) || [];
      const shadowUser = { ...user, password: hashPassword(password) };
      const shadowIndex = shadowUsers.findIndex(u => u.email === email);
      if (shadowIndex >= 0) {
        shadowUsers[shadowIndex] = shadowUser;
      } else {
        shadowUsers.push(shadowUser);
      }
      localStorage.setItem('sportsscraper_users', JSON.stringify(shadowUsers));
      return { success: true, user };
    }

    let payload = {};
    try { payload = await response.json(); } catch (_) {}
    return { success: false, error: payload.error || 'Error registrando usuario' };
  } catch (e) {
    // Fallback to local
    const newUser = normalizeUser({
      id: 'user_' + Date.now(),
      email: email,
      name: name,
      password: hashPassword(password),
      createdAt: new Date().toISOString(),
    });
    users.push(newUser);
    localStorage.setItem('sportsscraper_users', JSON.stringify(users));
    return { success: true, user: newUser };
  }
}

async function loginUser(email, password) {
  email = (email || '').trim().toLowerCase();
  if (!email || !password) {
    return { success: false, error: 'Email y contraseña requeridos' };
  }
  // Try backend login first
  try {
    const response = await fetch(`${window.API_BASE}/api/auth/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const payload = await response.json();
    if (response.ok && payload.token) {
      const normalizedUser = normalizeUser(payload.user);
      const shadowUsers = JSON.parse(localStorage.getItem('sportsscraper_users')) || [];
      const shadowUser = { ...normalizedUser, password: hashPassword(password) };
      const shadowIndex = shadowUsers.findIndex(u => u.email === email);
      if (shadowIndex >= 0) {
        shadowUsers[shadowIndex] = shadowUser;
      } else {
        shadowUsers.push(shadowUser);
      }
      localStorage.setItem('sportsscraper_users', JSON.stringify(shadowUsers));
      localStorage.setItem('sportsscraper_token', payload.token);
      localStorage.setItem('sportsscraper_current_user', JSON.stringify(normalizedUser));
      localStorage.setItem('sportsscraper_session', JSON.stringify({ userId: normalizedUser.id, loggedIn: true, loginTime: new Date().toISOString() }));
      return { success: true, user: normalizedUser };
    }

    // fallback to local verification if API rejects
    const users = JSON.parse(localStorage.getItem('sportsscraper_users')) || [];
    const user = users.find(u => u.email === email);
    if (!user) return { success: false, error: payload.error || 'Email no encontrado' };
    if (user.password !== hashPassword(password)) return { success: false, error: 'Contraseña incorrecta' };
    const normalizedLocalUser = normalizeUser(user);
    localStorage.setItem('sportsscraper_session', JSON.stringify({ userId: normalizedLocalUser.id, loggedIn: true, loginTime: new Date().toISOString() }));
    localStorage.setItem('sportsscraper_current_user', JSON.stringify(normalizedLocalUser));
    return { success: true, user: normalizedLocalUser };
  } catch (e) {
    // Fallback local
    const users = JSON.parse(localStorage.getItem('sportsscraper_users')) || [];
    const user = users.find(u => u.email === email);
    if (!user) return { success: false, error: 'Error de conexión y email no encontrado' };
    if (user.password !== hashPassword(password)) return { success: false, error: 'Contraseña incorrecta' };
    const normalizedLocalUser = normalizeUser(user);
    localStorage.setItem('sportsscraper_session', JSON.stringify({ userId: normalizedLocalUser.id, loggedIn: true, loginTime: new Date().toISOString() }));
    localStorage.setItem('sportsscraper_current_user', JSON.stringify(normalizedLocalUser));
    return { success: true, user: normalizedLocalUser };
  }
}

function logoutUser() {
  localStorage.removeItem('sportsscraper_session');
  localStorage.removeItem('sportsscraper_current_user');
}

function getCurrentUser() {
  const session = JSON.parse(localStorage.getItem('sportsscraper_session'));

  if (!session || !session.loggedIn) {
    return null;
  }

  const user = JSON.parse(localStorage.getItem('sportsscraper_current_user'));
  return normalizeUser(user);
}

function isLoggedIn() {
  const session = JSON.parse(localStorage.getItem('sportsscraper_session'));
  return session && session.loggedIn;
}

function getAuthToken() {
  return localStorage.getItem('sportsscraper_token') || '';
}

function updateUserProfile(name, email) {
  const user = getCurrentUser();
  if (!user) return false;

  const users = JSON.parse(localStorage.getItem('sportsscraper_users')) || [];
  const userIndex = users.findIndex(u => u.id === user.id);

  if (userIndex === -1) return false;

  users[userIndex].name = name;
  users[userIndex].email = email;

  localStorage.setItem('sportsscraper_users', JSON.stringify(users));
  localStorage.setItem('sportsscraper_current_user', JSON.stringify(users[userIndex]));

  return true;
}

async function changePassword(oldPassword, newPassword) {
  const user = getCurrentUser();
  if (!user) return { success: false, error: 'No hay usuario logueado' };

  const token = getAuthToken();
  if (token) {
    try {
      const response = await fetch(`${window.API_BASE}/api/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
      });

      const payload = await response.json().catch(() => ({}));
      if (response.ok) {
        const users = JSON.parse(localStorage.getItem('sportsscraper_users')) || [];
        const userIndex = users.findIndex(u => u.id === user.id);
        if (userIndex !== -1 && users[userIndex].password) {
          users[userIndex].password = hashPassword(newPassword);
          localStorage.setItem('sportsscraper_users', JSON.stringify(users));
        }
        return { success: true };
      }

      return { success: false, error: payload.error || 'No se pudo cambiar la contraseña' };
    } catch (error) {
      // Fall back to local storage only if the backend is unreachable.
    }
  }

  const users = JSON.parse(localStorage.getItem('sportsscraper_users')) || [];
  const storedUser = users.find(u => u.id === user.id) || user;

  if (storedUser.password !== hashPassword(oldPassword)) {
    return { success: false, error: 'Contraseña actual incorrecta' };
  }

  if (newPassword.length < 6) {
    return { success: false, error: 'La nueva contraseña debe tener al menos 6 caracteres' };
  }

  const userIndex = users.findIndex(u => u.id === user.id);

  if (userIndex === -1) {
    return { success: false, error: 'No se encontró el usuario para actualizar la contraseña' };
  }

  users[userIndex].password = hashPassword(newPassword);
  localStorage.setItem('sportsscraper_users', JSON.stringify(users));
  localStorage.setItem('sportsscraper_current_user', JSON.stringify(users[userIndex]));

  return { success: true };
}

// ========================================
// SESSION MANAGEMENT
// ========================================

function checkAndRestoreSession() {
  const session = JSON.parse(localStorage.getItem('sportsscraper_session'));
  if (session && session.loggedIn) {
    return true;
  }
  return false;
}
