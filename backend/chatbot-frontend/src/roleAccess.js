export const getRoleAccess = ({ userRole, isAdmin, isProfessor: isProfessorFlag }) => {
  const role = userRole || '';
  const isCentralAdmin = role === 'admin_central' || (isAdmin && (!userRole || userRole === 'admin_central'));
  const isGestionnaire = role === 'admin_gestionnaire';
  const isSecretary = role === 'secretaire_facultaire';
  const isProfessor = (role === 'professeur' || isProfessorFlag) && !isCentralAdmin;

  return {
    isCentralAdmin,
    isGestionnaire,
    isSecretary,
    isProfessor,
    canAccessChat: true,
    canAccessFaculties: isCentralAdmin || isGestionnaire,
    canManageGestionnaires: isCentralAdmin,
    canManageSecretaires: isGestionnaire || isCentralAdmin,
    canManageProfessors: isSecretary || isCentralAdmin,
    canManageCourses: isSecretary || isCentralAdmin,
    canManageStudents: isCentralAdmin || isGestionnaire,
    canManageNotes: isProfessor,
    canViewProgress: isProfessor || isCentralAdmin || isSecretary,
    canAccessAdminSystem: isCentralAdmin,
    canManageRoles: isCentralAdmin,
    canSeeFacultyData: isCentralAdmin || isGestionnaire || isSecretary,
    canManageTeachingContent: isProfessor || isCentralAdmin,
    isStudent: role === 'etudiant' || (!role && !isAdmin && !isProfessor && !isCentralAdmin),
  };
};

