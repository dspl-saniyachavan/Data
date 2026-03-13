export type Role = 'admin' | 'user';
export type Permission = 'view_dashboard' | 'manage_users' | 'view_profile' | 'manage_parameters';

const rolePermissions: Record<Role, Permission[]> = {
  admin: ['view_dashboard', 'manage_users', 'view_profile', 'manage_parameters'],
  user: ['view_dashboard', 'view_profile'],
};

export function hasPermission(role: Role, permission: Permission): boolean {
  return rolePermissions[role]?.includes(permission) || false;
}

export function hasRole(userRole: string, allowedRoles: Role[]): boolean {
  return allowedRoles.includes(userRole as Role);
}
