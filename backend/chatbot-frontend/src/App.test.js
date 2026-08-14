import { getRoleAccess } from './roleAccess';

describe('getRoleAccess', () => {
  it('gives full access to the central administrator', () => {
    const access = getRoleAccess({ userRole: 'admin_central', isAdmin: true, isProfessor: false });

    expect(access.canManageGestionnaires).toBe(true);
    expect(access.canManageSecretaires).toBe(true);
    expect(access.canManageProfessors).toBe(true);
    expect(access.canManageStudents).toBe(true);
    expect(access.canAccessAdminSystem).toBe(true);
  });

  it('restricts a student to the learning space', () => {
    const access = getRoleAccess({ userRole: 'etudiant', isAdmin: false, isProfessor: false });

    expect(access.canManageGestionnaires).toBe(false);
    expect(access.canManageSecretaires).toBe(false);
    expect(access.canManageProfessors).toBe(false);
    expect(access.canManageStudents).toBe(false);
    expect(access.canManageNotes).toBe(false);
    expect(access.canViewProgress).toBe(false);
    expect(access.canAccessChat).toBe(true);
  });

  it('allows a secretary to supervise professors and students within the faculty', () => {
    const access = getRoleAccess({ userRole: 'secretaire_facultaire', isAdmin: false, isProfessor: false });

    expect(access.canManageProfessors).toBe(true);
    expect(access.canManageStudents).toBe(true);
    expect(access.canAccessFaculties).toBe(true);
    expect(access.canManageSecretaires).toBe(false);
  });
});
