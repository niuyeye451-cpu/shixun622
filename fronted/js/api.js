/**
 * MedGraph AI - Shared API Module
 * Base URL: /api/v1
 * Auth: JWT Bearer tokens managed in sessionStorage
 */

const API_BASE = '/api/v1';

// ========== Token Management ==========

const Token = {
  get() {
    return sessionStorage.getItem('access_token');
  },
  set(token) {
    sessionStorage.setItem('access_token', token);
  },
  getRefresh() {
    return sessionStorage.getItem('refresh_token');
  },
  setRefresh(token) {
    sessionStorage.setItem('refresh_token', token);
  },
  clear() {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('user_info');
    sessionStorage.removeItem('user_type');
  },
  isLoggedIn() {
    return !!this.get();
  }
};

// ========== User Info ==========

const User = {
  set(info, type) {
    sessionStorage.setItem('user_info', JSON.stringify(info));
    sessionStorage.setItem('user_type', type);
  },
  get() {
    const info = sessionStorage.getItem('user_info');
    return info ? JSON.parse(info) : null;
  },
  type() {
    return sessionStorage.getItem('user_type');
  },
  clear() {
    sessionStorage.removeItem('user_info');
    sessionStorage.removeItem('user_type');
  }
};

// ========== API Request Helper ==========

/**
 * Unified API request function.
 * Handles auth headers, 401 refresh, error formatting.
 */
async function apiRequest(method, path, body = null, options = {}) {
  const url = API_BASE + path;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  const token = Token.get();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    method,
    headers,
    ...options.fetchOptions
  };

  if (body && method !== 'GET') {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(url, config);

  // Handle 401 - try refresh token
  if (response.status === 401 && Token.getRefresh()) {
    const refreshed = await refreshToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${Token.get()}`;
      const retryResponse = await fetch(url, { ...config, headers });
      return handleResponse(retryResponse);
    }
    // Refresh failed - redirect to login
    Token.clear();
    User.clear();
    window.location.href = 'page1.html';
    throw new Error('认证已过期，请重新登录');
  }

  return handleResponse(response);
}

async function handleResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || data.message || `HTTP ${response.status}`);
  }
  return data;
}

async function refreshToken() {
  try {
    const response = await fetch(API_BASE + '/common/auth/token/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: Token.getRefresh() })
    });
    const data = await response.json();
    if (data.code === 200 && data.data) {
      Token.set(data.data.access_token);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

// ========== Convenience Methods ==========

const API = {
  get(path) {
    return apiRequest('GET', path);
  },
  post(path, body) {
    return apiRequest('POST', path, body);
  },
  put(path, body) {
    return apiRequest('PUT', path, body);
  },
  delete(path) {
    return apiRequest('DELETE', path);
  },
  /**
   * Upload file with FormData
   */
  async upload(path, formData) {
    const url = API_BASE + path;
    const headers = {};
    const token = Token.get();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    });
    return handleResponse(response);
  }
};

// ========== Auth API ==========

const AuthAPI = {
  /** Send SMS verification code */
  sendSms(phone, type = 'login') {
    return API.post('/common/auth/sms/send', { phone, type });
  },

  /** Patient login with phone + code */
  async patientLogin(phone, code, smsId) {
    const res = await API.post('/common/auth/patient/login', {
      phone, code, sms_id: smsId
    });
    if (res.code === 200) {
      Token.set(res.data.access_token);
      Token.setRefresh(res.data.refresh_token);
      User.set(res.data.user_info, 'patient');
    }
    return res;
  },

  /** Doctor login with username + password */
  async doctorLogin(userName, passwordHash) {
    const res = await API.post('/common/auth/doctor/login', {
      user_name: userName, password_hash: passwordHash
    });
    if (res.code === 200) {
      Token.set(res.data.access_token);
      Token.setRefresh(res.data.refresh_token);
      User.set(res.data.user_info, 'doctor');
    }
    return res;
  },

  /** Admin login with username + password */
  async adminLogin(userName, passwordHash) {
    const res = await API.post('/common/auth/admin/login', {
      user_name: userName, password_hash: passwordHash
    });
    if (res.code === 200) {
      Token.set(res.data.access_token);
      Token.setRefresh(res.data.refresh_token);
      User.set(res.data.user_info, 'admin');
    }
    return res;
  },

  /** Logout */
  logout() {
    return API.post('/common/auth/logout');
  },

  /** Change password */
  changePassword(oldPwdHash, newPwdHash) {
    return API.put('/common/auth/password', {
      old_password_hash: oldPwdHash, new_password_hash: newPwdHash
    });
  }
};

// ========== Common API ==========

const CommonAPI = {
  /** Get department list */
  getDepartments(keyword) {
    const params = keyword ? `?keyword=${encodeURIComponent(keyword)}` : '';
    return API.get(`/common/departments${params}`);
  },

  /** Get hospital list */
  getHospitals(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/common/hospitals?${qs}`);
  },

  /** Upload image */
  uploadImage(file, scene = 'other') {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('scene', scene);
    return API.upload('/common/upload/image', fd);
  },

  /** Submit feedback */
  submitFeedback(data) {
    return API.post('/common/feedback', data);
  },

  /** Get disease graph */
  getDiseaseGraph(diseaseName, depth = 2) {
    return API.get(`/common/graph/disease/${encodeURIComponent(diseaseName)}?depth=${depth}`);
  },

  /** Search entities */
  searchEntities(keyword, entityType, limit = 10) {
    const params = new URLSearchParams({ keyword, limit });
    if (entityType) params.set('entity_type', entityType);
    return API.get(`/common/graph/entities/search?${params}`);
  },

  /** Get entity detail */
  getEntityDetail(entityId) {
    return API.get(`/common/graph/entities/${entityId}`);
  },

  /** Query entity relations */
  queryRelations(sourceEntity, targetEntity, maxDepth = 3) {
    const params = new URLSearchParams({ source_entity: sourceEntity, target_entity: targetEntity, max_depth: maxDepth });
    return API.get(`/common/graph/relations?${params}`);
  }
};

// ========== Patient API ==========

const PatientAPI = {
  // --- Consultation ---
  /** Create a new conversation */
  createConversation(sessionType, initialMessage) {
    return API.post('/patient/consultation/conversations', {
      session_type: sessionType,
      initial_message: initialMessage
    });
  },

  /** Send message in conversation */
  sendMessage(conversationId, content, imageIds) {
    return API.post(`/patient/consultation/conversations/${conversationId}/messages`, {
      content, image_ids: imageIds || []
    });
  },

  /** Get conversation messages */
  getMessages(conversationId, lastMessageId, limit = 20) {
    const params = new URLSearchParams({ limit });
    if (lastMessageId) params.set('last_message_id', lastMessageId);
    return API.get(`/patient/consultation/conversations/${conversationId}/messages?${params}`);
  },

  /** End conversation */
  endConversation(conversationId) {
    return API.put(`/patient/consultation/conversations/${conversationId}/end`);
  },

  /** Get conversation list */
  getConversations(page = 1, pageSize = 10, sessionType) {
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (sessionType) params.set('session_type', sessionType);
    return API.get(`/patient/consultation/conversations?${params}`);
  },

  /** Quick symptom query */
  quickSymptomQuery(symptomText, age, gender) {
    return API.post('/patient/consultation/symptom/quick', {
      symptom_text: symptomText, age, gender
    });
  },

  /** Get disease graph (patient version) */
  getDiseaseGraph(diseaseId) {
    return API.get(`/patient/consultation/disease/${diseaseId}/graph`);
  },

  // --- Recommendation ---
  /** Recommend department based on symptoms */
  recommendDepartment(symptoms, duration, severity) {
    return API.post('/patient/recommendation/department', {
      symptoms, duration, severity
    });
  },

  /** Recommend hospitals */
  recommendHospitals(departmentId, city) {
    const params = new URLSearchParams({ department_id: departmentId });
    if (city) params.set('city', city);
    return API.get(`/patient/recommendation/hospitals?${params}`);
  },

  /** Recommend doctors */
  recommendDoctors(departmentId, hospitalId) {
    const params = new URLSearchParams({ department_id: departmentId });
    if (hospitalId) params.set('hospital_id', hospitalId);
    return API.get(`/patient/recommendation/doctors?${params}`);
  },

  // --- Registration ---
  /** Get registration slots */
  getSlots(doctorId, date) {
    const params = new URLSearchParams({ doctor_id: doctorId });
    if (date) params.set('date', date);
    return API.get(`/patient/registration/slots?${params}`);
  },

  /** Create registration */
  register(data) {
    return API.post('/patient/registration', data);
  },

  /** Get registration list */
  getRegistrations(status, page = 1, pageSize = 10) {
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (status) params.set('status', status);
    return API.get(`/patient/registration?${params}`);
  },

  /** Cancel registration */
  cancelRegistration(registrationId) {
    return API.put(`/patient/registration/${registrationId}/cancel`);
  },

  // --- Profile ---
  /** Get patient profile */
  getProfile() {
    return API.get('/patient/profile');
  },

  /** Update patient profile */
  updateProfile(data) {
    return API.put('/patient/profile', data);
  },

  // --- History ---
  /** Get consultation history */
  getConsultationHistory(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/patient/history/consultations?${qs}`);
  },

  /** Get consultation detail */
  getConsultationDetail(consultationId) {
    return API.get(`/patient/history/consultations/${consultationId}`);
  },

  // --- Reminders ---
  /** Get reminders */
  getReminders(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/patient/reminders?${qs}`);
  },

  /** Mark reminder read */
  markReminderRead(reminderId) {
    return API.put(`/patient/reminders/${reminderId}/read`);
  },

  /** Mark all reminders read */
  markAllRead() {
    return API.put('/patient/reminders/read-all');
  }
};

// ========== Doctor API ==========

const DoctorAPI = {
  // --- Case Assist ---
  /** Create case conversation */
  createCaseConversation(caseType, patientInfo, initialQuery) {
    return API.post('/doctor/consultation/conversations', {
      case_type: caseType,
      patient_info: patientInfo,
      initial_query: initialQuery
    });
  },

  /** Send case message */
  sendCaseMessage(conversationId, content) {
    return API.post(`/doctor/consultation/conversations/${conversationId}/messages?content=${encodeURIComponent(content)}`);
  },

  /** Get case conversation messages */
  getCaseMessages(conversationId, lastMessageId, limit = 20) {
    const params = new URLSearchParams({ limit });
    if (lastMessageId) params.set('last_message_id', lastMessageId);
    return API.get(`/doctor/consultation/conversations/${conversationId}/messages?${params}`);
  },

  /** End case conversation */
  endCaseConversation(conversationId) {
    return API.put(`/doctor/consultation/conversations/${conversationId}/end`);
  },

  /** Get case conversation list */
  getCaseConversations(page = 1, pageSize = 10, caseType) {
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (caseType) params.set('case_type', caseType);
    return API.get(`/doctor/consultation/conversations?${params}`);
  },

  /** Multi-symptom analysis */
  analyzeMultiSymptom(diseases, symptoms, analysisDepth = 3) {
    return API.post('/doctor/consultation/multi-symptom', {
      diseases, symptoms, analysis_depth: analysisDepth
    });
  },

  /** Differential diagnosis */
  differentialDiagnosis(chiefComplaint, symptoms, patientInfo, examResults) {
    return API.post('/doctor/consultation/differential-diagnosis', {
      chief_complaint: chiefComplaint,
      symptoms,
      patient_info: patientInfo,
      exam_results: examResults
    });
  },

  // --- Knowledge ---
  /** Query knowledge */
  queryKnowledge(query, queryType, context) {
    return API.post('/doctor/knowledge/query', {
      query, query_type: queryType, context
    });
  },

  /** Check drug interactions */
  checkDrugInteraction(drugIds, drugNames) {
    return API.post('/doctor/knowledge/drug-interaction', {
      drug_ids: drugIds, drug_names: drugNames
    });
  },

  // --- Profile ---
  /** Get doctor profile */
  getProfile() {
    return API.get('/doctor/profile');
  },

  /** Update doctor profile */
  updateProfile(data) {
    return API.put('/doctor/profile', data);
  },

  // --- Feedback ---
  /** Submit doctor feedback */
  submitFeedback(data) {
    return API.post('/doctor/feedback', data);
  },

  /** Get doctor feedback list */
  getFeedbackList(status, page = 1, pageSize = 10) {
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (status) params.set('status', status);
    return API.get(`/doctor/feedback?${params}`);
  }
};

// ========== Admin API ==========

const AdminAPI = {
  // --- Users ---
  /** Get patient list */
  getPatients(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/users/patients?${qs}`);
  },

  /** Get patient detail */
  getPatientDetail(patientId) {
    return API.get(`/admin/users/patients/${patientId}`);
  },

  /** Update patient status */
  updatePatientStatus(patientId, status, reason) {
    return API.put(`/admin/users/patients/${patientId}/status`, { status, reason });
  },

  /** Get doctor list */
  getDoctors(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/users/doctors?${qs}`);
  },

  /** Create doctor */
  createDoctor(data) {
    return API.post('/admin/users/doctors', data);
  },

  /** Get doctor detail */
  getDoctorDetail(doctorId) {
    return API.get(`/admin/users/doctors/${doctorId}`);
  },

  /** Update doctor status */
  updateDoctorStatus(doctorId, status, reason) {
    return API.put(`/admin/users/doctors/${doctorId}/status`, { status, reason });
  },

  /** Get admin list */
  getAdmins(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/users/admins?${qs}`);
  },

  // --- Knowledge Entities ---
  /** Create entity */
  createEntity(data) {
    return API.post('/admin/knowledge/entities', data);
  },

  /** Get entity list */
  getEntities(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/knowledge/entities?${qs}`);
  },

  /** Get entity detail */
  getEntityDetail(entityId) {
    return API.get(`/admin/knowledge/entities/${entityId}`);
  },

  /** Update entity */
  updateEntity(entityId, data) {
    return API.put(`/admin/knowledge/entities/${entityId}`, data);
  },

  /** Delete entity */
  deleteEntity(entityId) {
    return API.delete(`/admin/knowledge/entities/${entityId}`);
  },

  // --- Relations ---
  /** Create relation */
  createRelation(data) {
    return API.post('/admin/knowledge/relations', data);
  },

  /** Get relation list */
  getRelations(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/knowledge/relations?${qs}`);
  },

  /** Delete relation */
  deleteRelation(relationId) {
    return API.delete(`/admin/knowledge/relations/${relationId}`);
  },

  // --- Synonyms ---
  /** Create synonym */
  createSynonym(data) {
    return API.post('/admin/knowledge/synonyms', data);
  },

  /** Get synonym list */
  getSynonyms(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/knowledge/synonyms?${qs}`);
  },

  /** Delete synonym */
  deleteSynonym(synonymId) {
    return API.delete(`/admin/knowledge/synonyms/${synonymId}`);
  },

  // --- Versions ---
  /** Create version */
  createVersion(data) {
    return API.post('/admin/knowledge/versions', data);
  },

  /** Get version list */
  getVersions(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/knowledge/versions?${qs}`);
  },

  /** Publish version */
  publishVersion(versionId) {
    return API.put(`/admin/knowledge/versions/${versionId}/publish`);
  },

  // --- Feedbacks ---
  /** Get feedback list */
  getFeedbacks(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/feedbacks?${qs}`);
  },

  /** Get feedback detail */
  getFeedbackDetail(feedbackId) {
    return API.get(`/admin/feedbacks/${feedbackId}`);
  },

  /** Reply to feedback */
  replyFeedback(feedbackId, reply) {
    return API.put(`/admin/feedbacks/${feedbackId}/reply?reply=${encodeURIComponent(reply)}`);
  },

  // --- Unknown Questions ---
  /** Get unknown questions */
  getUnknownQuestions(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return API.get(`/admin/unknown-questions?${qs}`);
  },

  /** Get unknown question detail */
  getUnknownQuestionDetail(questionId) {
    return API.get(`/admin/unknown-questions/${questionId}`);
  },

  /** Resolve unknown question */
  resolveUnknownQuestion(questionId, data) {
    return API.put(`/admin/unknown-questions/${questionId}/resolve`, data);
  },

  /** Batch resolve unknown questions */
  batchResolveQuestions(data) {
    return API.post('/admin/unknown-questions/batch-resolve', data);
  },

  // --- Statistics ---
  /** Get dashboard statistics */
  getDashboardStats() {
    return API.get('/admin/statistics/dashboard');
  },

  /** Get consultation statistics */
  getConsultationStats(startDate, endDate, dimension = 'day') {
    return API.get(`/admin/statistics/consultations?start_date=${startDate}&end_date=${endDate}&dimension=${dimension}`);
  },

  /** Get feedback statistics */
  getFeedbackStats(startDate, endDate) {
    return API.get(`/admin/statistics/feedback?start_date=${startDate}&end_date=${endDate}`);
  },

  /** Get knowledge statistics */
  getKnowledgeStats() {
    return API.get('/admin/statistics/knowledge');
  }
};

// ========== Utility Functions ==========

/** Simple MD5 hash for password (matches backend expectations) */
function md5Hash(str) {
  // Use a simple hash function - in production use a proper MD5 library
  // For demo purposes, we use a simple hash
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(8, '0');
}

/** Show a toast/notification message */
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  const colors = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    warning: 'bg-yellow-500',
    info: 'bg-primary'
  };
  toast.className = `fixed top-4 right-4 z-[9999] ${colors[type] || colors.info} text-white px-md py-sm rounded-lg shadow-lg font-label-md text-label-md animate-fade-in`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/** Check auth and redirect to login if not logged in */
function requireAuth() {
  if (!Token.isLoggedIn()) {
    window.location.href = 'page1.html';
    return false;
  }
  return true;
}

/** Check if user is specific type, redirect if not */
function requireRole(role) {
  if (!requireAuth()) return false;
  if (User.type() !== role) {
    showToast('无权限访问此页面', 'error');
    const redirects = {
      patient: 'page2.html',
      doctor: 'page3.html',
      admin: 'page4.html'
    };
    window.location.href = redirects[User.type()] || 'page1.html';
    return false;
  }
  return true;
}

/** Format date string */
function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  });
}

/** Get query parameter value */
function getQueryParam(name) {
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}
