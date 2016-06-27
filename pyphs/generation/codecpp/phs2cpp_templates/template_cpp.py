# -*- coding: utf-8 -*-
"""
Created on Fri Mar  4 02:17:30 2016

@author: Falaize
"""

def str_accesors_presolve(phs):
    def str_get_int(var):
        return "const unsigned int " + class_ref(phs) + "get_"+var+"() const {"+\
        "\n    return "+var+";\n}\n"

    def str_get_vec(var, dim):
        return \
            """vector<double> """+class_ref(phs)+"""get_"""+var+"""() const {
    vector<double> v = vector<double>("""+dim+""");
     for (int i=0; i<get_"""+dim+"""(); i++) {
        v[i] = """+var+"""[i];
     }
    return v;
}
"""
    str_accesors = "\n// Accesors to private variables\n\n"
    str_accesors += str_get_int('nx')
    str_accesors += str_get_int('nxl')
    str_accesors += str_get_int('nxnl')
    str_accesors += str_get_int('nw')
    str_accesors += str_get_int('nwl')
    str_accesors += str_get_int('nwnl')
    str_accesors += str_get_int('ny')
    str_accesors += str_get_int('np')
    str_accesors += str_get_vec('u', 'ny')
    str_accesors += str_get_vec('y', 'ny')
    str_accesors += str_get_vec('x', 'nx')
    str_accesors += str_get_vec('dx', 'nx')
    str_accesors += str_get_vec('dxH', 'nx')
    str_accesors += str_get_vec('w', 'nw')
    str_accesors += str_get_vec('z', 'ny')
    return str_accesors

def str_modificators_presolve(phs):
    def str_set(var):
        return "void "+class_ref(phs)+"set_"+var+"(vector<double> v) {\n    "+var+" = v; \n}\n"
    str_modificators = "\n// Mutators of private variables\n"
    str_modificators += str_set('u')
    str_modificators += str_set('x')
    return str_modificators

def str_functions_presolve(phs):

    dict_args = {"x":phs.symbs.x, "dx": phs.dx, "w": phs.symbs.w, "u": phs.symbs.u, "p": phs.symbs.p}
    phs_label = phs.label.upper()

    from ..phs2cpp import Expr2Cpp
    exprcpp = lambda e, lf, lv: Expr2Cpp(e, dict_args, phs_label, lf, lv, "c")

    str_phs_functions = "\n// Port-Hamiltonian runtime functions\n"

    expr = list(phs.Fl)
    str_dxl = ["dx["+str(n)+"]" for n in range(phs.dims.xl)]
    str_mat_wl = ["w["+str(n)+"]" for n in range(phs.dims.wl)]
    label_variable = str_dxl + str_mat_wl
    label_func = "Fl"
    str_phs_functions += exprcpp(expr, label_func, label_variable)

    if phs.isNL:
        from sympy import Matrix
        expr = list(Matrix(phs.dxnl()+phs.symbs.wnl())+Matrix(phs.Fnl))
        str_dxl = ["dx["+str(phs.dims.xl+n)+"]" for n in range(phs.dims.xnl())]
        str_mat_wl = ["wnl["+str(phs.dims.wl+n)+"]" for n in range(phs.dims.wnl())]
        label_variable = str_dxl + str_mat_wl
        label_func = "Fnl"
        str_phs_functions += exprcpp(expr, label_func, label_variable)

        expr = [phs.Fnl_residual]
        label_variable = "residual_NR"
        label_func = "FresidualNR"
        str_phs_functions += exprcpp(expr, label_func, label_variable).replace('residual_NR[0] ', 'residual_NR ')

    expr = phs.exprs.dxHd
    label_variable = "dxH"
    label_func = "FdxH"
    str_phs_functions += exprcpp(expr, label_func, label_variable)

    expr = phs.exprs.z
    label_variable = "z"
    label_func = "Fz"
    str_phs_functions += exprcpp(expr, label_func, label_variable)

    expr = phs.Fy
    label_variable = "y"
    label_func = "Fy"
    str_phs_functions += exprcpp(expr, label_func, label_variable)
    return str_phs_functions

def str_process_presolve(phs):

    phs_label = phs.label.upper()
    if phs.isNL:
        str_newton_solver = \
    """
            // Newton-Raphson iteration
            it = 0;
            residual_NR = 1;
            while ((it<NbItNR) & (residual_NR>eps)) {
                Fnl();
                FresidualNR();
                it++;
            }
    """
    else:
        str_newton_solver = ""

    str_process = "void "+phs_label+"::process(vector<double>& In, vector<double>& parameters) {\n "+\
    """

        u = In;
        p = parameters;
    """ + str_newton_solver + \
    """
        Fl();
        FdxH();
        Fz();
        Fy();
        for (unsigned int i=0; i<get_nx(); i++ ) {
            x[i] += dx[i];
        }
    """ +"}\n"
    return str_process


def cfile_presolve(phs):

    str_includes = '#include "'+phs.paths['cpp']+"/" + ('phobj').upper() + '.h"\n\n'

    str_constructor = "\n// Default Constructor:\n"+class_ref(phs)+phs.label.upper()+"() {\n}\n"

    str_initx_constructor = "\n// Constructor Initializing x:\n"+class_ref(phs)+\
                        phs.label.upper()+"(vector<double>& x0) {\n"  +\
                        '    if (x.size() == x0.size()) {\n        x = x0;\n    }\n    else {\n        cerr << "Size of x0 does not match size of x" << endl;\n        exit(1);\n    }\n}\n'

    str_destructor = "\n// Default Destructor:\n"+class_ref(phs)+ "~"+phs.label.upper()+"() {\n\n}\n"

    str_c = ""
    str_c += str_includes
    str_c += str_constructor
    str_c += str_process_presolve(phs)
    str_c += str_initx_constructor+str_destructor
    str_c += str_accesors_presolve(phs)
    str_c += str_modificators_presolve(phs)
    str_c += str_functions_presolve(phs)

    c_file = open(phs.paths['cpp']+"/"+"phobj.cpp", 'w')
    c_file.write(str_c)
    c_file.close()

    return str_c


###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################
###########################################################################


def class_ref(phs):
    return phs.label.upper()+"::"

def str_accesors_full(phs):

    def str_get_int(var):
        strget = "const unsigned int "+class_ref(phs)+"get_"+var+"() const {\n    return "+var+";\n}\n"
        return strget
    def str_get_vec(var, dim):
        return \
"""\nvector<double> """+class_ref(phs)+"""get_"""+var+"""() const {
    vector<double> v = vector<double>("""+dim+""");
     for (int i=0; i<get_"""+dim+"""(); i++) {
        v[i] = """+var+"""[i];
    }
    return v;
}
"""

    str_accesors = "\n// Accesors to private variables\n\n"

    str_accesors += str_get_int('nx')
    str_accesors += str_get_int('nxl')
    str_accesors += str_get_int('nxnl')

    str_accesors += str_get_int('nw')
    str_accesors += str_get_int('nwl')
    str_accesors += str_get_int('nwnl')

    str_accesors += str_get_int('ny')

    str_accesors += str_get_int('np')

    str_accesors += str_get_vec('u', 'ny')
    str_accesors += str_get_vec('y', 'ny')

    str_accesors += str_get_vec('x', 'nx')
    str_accesors += str_get_vec('dx', 'nx')
    str_accesors += str_get_vec('dxH', 'nx')

    str_accesors += str_get_vec('w', 'nw')
    str_accesors += str_get_vec('z', 'nw')

    return str_accesors

def str_functions_full(phs):

    str_phs_functions = "\n// Port-Hamiltonian runtime functions\n"

    dict_args = {"x":phs.symbs.x, "dx": phs.symbs.dx(), "w": phs.symbs.w, "u": phs.symbs.u, "p": phs.symbs.p}
    phs_label = phs.label.upper()
    def exprcpp(expr, func_label, var_label):
        from ..phs2cpp import Expr2Cpp
        return Expr2Cpp(expr, dict_args, phs_label, func_label, var_label, "c")
    def matcpp(mat_expr, func_label, mat_label):
        from ..phs2cpp import Matrix2Cpp
        return Matrix2Cpp(mat_expr, dict_args, phs_label, func_label, mat_label, "c")
    def shortmatcpp(obj, name):
        from pyphs.misc.tools import geteval
        mat_expr = geteval(obj, name)
        func_label = 'UpDate_' + name
        return matcpp(mat_expr, func_label, name)

    str_xl = "A7*xl()" if phs.dims.xl > 0 else ""
    str_xnl = " + " if (phs.dims.xl > 0) and (phs.dims.xnl() > 0) else ""
    str_xnl += "B7*dxHnl()" if phs.dims.xnl() > 0 else ""
    str_wnl = " + " if (phs.dims.x()> 0) and (phs.dims.wnl() > 0) else ""
    str_wnl += "C7*znl()" if phs.dims.wnl() > 0 else ""
    str_u = " + " if ((phs.dims.x()+phs.dims.wnl()) > 0) and (phs.dims.y() > 0) else ""
    str_u += "D7*u" if phs.dims.y() > 0 else ""

    if (phs.dims.xl+phs.dims.wl) > 0:
        str_update_lin = "void "+class_ref(phs)+"UpDate_l() {\n    Fl << " + str_xl + str_xnl + str_wnl + str_u + "; \n    for(int i=0; i<get_nxl(); i++){\n        dx[i] = Fl[i];\n    }\n    for(int i=0; i<get_nwl(); i++){\n        w[i] = Fl[i+get_nxl()];\n    }\n}\n"
    else:
        str_update_lin = "void "+class_ref(phs)+"UpDate_l() {\n}\n"

    str_phs_functions += str_update_lin

    expr = phs.exprs.dxHd
    label_variable = "dxH"
    label_func = "UpDate_dxH"
    str_phs_functions += exprcpp(expr, label_func, label_variable)

    expr = phs.exprs.z
    label_variable = "z"
    label_func = "UpDate_z"
    str_phs_functions += exprcpp(expr, label_func, label_variable)

    expr = phs.exprs.yd
    label_variable = "y"
    label_func = "UpDate_y"
    str_phs_functions += exprcpp(expr, label_func, label_variable)

    names = ('xl', 'xnl', 'wl', 'wnl', 'y')
    for namei in names:
        for namej in names:
            str_phs_functions += shortmatcpp(phs.struc, 'J'+namei+namej)
    str_phs_functions += shortmatcpp(phs.exprs, 'R')
    str_phs_functions += shortmatcpp(phs.exprs, 'Q')

    if phs.dims.xl + phs.dims.wl:
        str_phs_functions += str_nonlinear_functions_full(phs, matcpp)

    return str_phs_functions

def str_pointer_full(phs):
    str_phs_functions = "\nMatrix<double,"+str(phs.dims.xl)+","+str(1)+"> "+class_ref(phs)+"xl(){\n    return Map<Matrix<double,"+str(phs.dims.xl)+",1>>(pointer_xl); \n}\n\n"
    str_phs_functions += "Matrix<double,"+str(phs.dims.xl)+","+str(1)+"> "+class_ref(phs)+"dxl(){\n    return Map<Matrix<double,"+str(phs.dims.xl)+",1>>(pointer_dxl); \n}\n\n"
    str_phs_functions += "Matrix<double,"+str(phs.dims.xl)+","+str(1)+"> "+class_ref(phs)+"dxHl(){\n    return Map<Matrix<double,"+str(phs.dims.xl)+",1>>(pointer_dxHl); \n}\n\n"
    if phs.dims.wl > 0:
        str_phs_functions += "Matrix<double,"+str(phs.dims.wl)+","+str(1)+"> "+class_ref(phs)+"wl(){\n    return Map<Matrix<double,"+str(phs.dims.wl)+",1>>(pointer_wl);\n}\n\n"
        str_phs_functions += "Matrix<double,"+str(phs.dims.wl)+","+str(1)+"> "+class_ref(phs)+"zl(){\n    return Map<Matrix<double,"+str(phs.dims.wl)+",1>>(pointer_zl);\n}\n\n"
    return str_phs_functions

def str_nonlinear_functions_full(phs, matcpp):
    str_phs_functions = ""
    expr = phs.exprs.impfunc
    label_variable = 'Fnl'
    label_func = "UpDate_Fnl"
    str_phs_functions += matcpp(expr, label_func, label_variable)

    expr = phs.exprs.jac_impfunc
    label_variable = 'JacobianFnl'
    label_func = "UpDate_JacobianFnl"
    str_phs_functions += matcpp(expr, label_func, label_variable)

    if phs.dims.xnl() > 0 and phs.dims.wnl() > 0:
        str_jacobian_nl_update = "    Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+","+str(phs.dims.xnl()+phs.dims.wnl())+"> eye;\n    Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+","+str(phs.dims.xnl()+phs.dims.wnl())+"> B;\n"+\
        "    eye << Matrix<double, "+str(phs.dims.xnl())+", "+str(phs.dims.xnl())+">::Identity() * fs , Matrix<double, "+str(phs.dims.xnl())+", "+str(phs.dims.wnl())+">::Zero() , Matrix<double, "+str(phs.dims.wnl())+", "+str(phs.dims.xnl())+">::Zero() , Matrix<double, " +str(phs.dims.wnl())+", "+str(phs.dims.wnl())+">::Identity(); " +\
        "    B << Bxnl, Bwnl;\n"
        str_update_nonlinear = "void "+class_ref(phs)+"UpDate_nl() {\n    Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+", "+str(1)+"> varnl;\n    varnl << dxnl(), wnl();\n    varnl -= iJacobianImplicitFunc()* ImpFunc;\n    for(int i=0; i<get_nxnl(); i++){\n        dx[i+get_nxl()] = varnl[i];\n    }\n    for(int i=0; i<get_nwnl(); i++){\n        w[i] = varnl[i+get_nxnl()];\n    }\n}\n"
    elif phs.dims.xnl() > 0 and phs.dims.wnl() == 0:
        str_jacobian_nl_update = "    Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+","+str(phs.dims.xnl()+phs.dims.wnl())+"> eye;\n    Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+","+str(phs.dims.xnl()+phs.dims.wnl())+"> B;\n"+\
        "    eye << Matrix<double, "+str(phs.dims.xnl())+", "+str(phs.dims.xnl())+">::Identity() * fs; " +\
         "    B << Bxnl;\n"
        str_update_nonlinear = "void "+class_ref(phs)+"UpDate_nl() {\n    Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+", "+str(1)+"> varnl;\n    varnl  << dxnl();\n    varnl -= iJacobianImplicitFunc()* ImpFunc;\n    for(int i=0; i<get_nxnl(); i++){\n        dx[i+get_nxl()] = varnl[i];\n    }\n}\n"
    elif phs.dims.xnl() == 0 and phs.dims.wnl() > 0:
        str_jacobian_nl_update = " Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+","+str(phs.dims.xnl()+phs.dims.wnl())+"> eye;\n    Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+","+str(phs.dims.xnl()+phs.dims.wnl())+"> B;\n"+\
        "    eye << Matrix<double, "+str(phs.dims.wnl())+", "+str(phs.dims.wnl())+">::Identity(); " +\
         "    B << Bwnl;\n"
        str_update_nonlinear = "void "+class_ref(phs)+"UpDate_nl() {\n    Matrix<double, "+str(phs.dims.xnl()+phs.dims.wnl())+", "+str(1)+"> varnl;\n    varnl  << wnl();\n    varnl -= iJacobianImplicitFunc()* ImpFunc;\n    for(int i=0; i<get_nwnl(); i++){\n        w[i+get_nwl()] = varnl[i+get_nxnl()];\n    }\n}\n"

    str_phs_functions += str_update_nonlinear
    str_jacobian_nl_update += "    JacobianImplicitFunc << eye - B*JacobianFnl; \n" + "    return JacobianImplicitFunc.inverse();"

    str_phs_functions += "Matrix<double,"+str(phs.dims.xnl()+phs.dims.wnl())+","+str(phs.dims.xnl()+phs.dims.wnl())+"> "+class_ref(phs)+"iJacobianImplicitFunc(){\n"+str_jacobian_nl_update+"\n}\n\n"

    str_phs_functions += "void "+class_ref(phs)+"UpDate_residualNR(){\n    residual_NR = sqrt(ImpFunc.transpose()*ImpFunc); }\n\n"
    str_xl4 = " - A4*xl() " if phs.dims.xl > 0 else ""
    str_xl5 = " - A5*xl() " if phs.dims.xl > 0 else ""
    if phs.dims.xnl() > 0 and phs.dims.wnl() > 0:
        str_implicit_func = "ImpFunc << fs*dxnl() " +str_xl4+" - Bxnl*Fnl - D4*u, wnl() " +str_xl5+" + Bwnl*Fnl + D5*u"
    elif phs.dims.xnl() > 0 and phs.dims.wnl() == 0:
        str_implicit_func = "ImpFunc << fs*dxnl() " +str_xl4+" - Bxnl*Fnl - D4*u"
    elif phs.dims.xnl() == 0 and phs.dims.wnl() > 0:
        str_implicit_func = "ImpFunc << wnl() " +str_xl5+" + Bwnl*Fnl + D5*u"

    str_phs_functions += "void "+class_ref(phs)+"UpDate_ImpFunc(){\n    " + str_implicit_func + "; \n}\n"

    if phs.dims.xnl() > 0:
        str_phs_functions += "Matrix<double,"+str(phs.dims.xnl())+","+str(1)+"> "+class_ref(phs)+"xnl(){\n    return Map<Matrix<double,"+str(phs.dims.xnl())+",1>>(pointer_xnl); \n}\n\n"
        str_phs_functions += "Matrix<double,"+str(phs.dims.xnl())+","+str(1)+"> "+class_ref(phs)+"dxnl(){\n    return Map<Matrix<double,"+str(phs.dims.xnl())+",1>>(pointer_dxnl); \n}\n\n"
        str_phs_functions += "Matrix<double,"+str(phs.dims.xnl())+","+str(1)+"> "+class_ref(phs)+"dxHnl(){\n    return Map<Matrix<double,"+str(phs.dims.xnl())+",1>>(pointer_dxHnl); \n}\n\n"
    if phs.dims.wnl() > 0:
        str_phs_functions += "Matrix<double,"+str(phs.dims.wnl())+","+str(1)+"> "+class_ref(phs)+"wnl(){\n    return Map<Matrix<double,"+str(phs.dims.wnl())+",1>>(pointer_wnl); \n}\n\n"
        str_phs_functions += "Matrix<double,"+str(phs.dims.wnl())+","+str(1)+"> "+class_ref(phs)+"znl(){\n    return Map<Matrix<double,"+str(phs.dims.wnl())+",1>>(pointer_znl); \n}\n\n"
    return str_phs_functions

def str_process_full(phs):
    if phs.dims.xl + phs.dims.wl > 0:
        str_newton_solver = \
    """
// Newton-Raphson iteration
it = 0;
residual_NR = 1;
 while ((it<NbItNR) & (residual_NR>eps)) {
    UpDate_Fnl();
    UpDate_JacobianFnl();
    UpDate_ImpFunc();
    UpDate_nl();
    UpDate_residualNR();
    it++;
}\n    //if(residual_NR>eps){cout << "residual_NR=" << residual_NR << endl ;}
    """
    else:
        str_newton_solver = ""

    if phs.dims.wl > 0:
        str_mat_wl = """\n    iDw << Matrix<double, """+str(phs.dims.wl)+", "+str(phs.dims.wl)+""">::Identity() - Jwlwl*R;
    Dw << iDw.inverse();"""
        if phs.dims.xl > 0:
            str_mat_wl += "\n    A1 << Dw*Jwlxl;"
        if phs.dims.xnl() > 0:
            str_mat_wl += "\n    B1 << Dw*Jwlxnl;"
        if phs.dims.wnl() > 0:
            str_mat_wl += "\n    C1 << Dw*Jwlwnl;"
        if phs.dims.y() > 0:
            str_mat_wl += "\n    D1 << Dw*Jwly;"
    else:
        str_mat_wl = ""

    if phs.dims.xl > 0:

        str_mat_xl = """
    tildeA2 << Jxlxl+Jxlwl*R*A1;
    tildeB2 << Jxlxnl+Jxlwl*R*B1;
    tildeC2 << Jxlwnl+Jxlwl*R*C1;
    tildeD2 << Jxly+Jxlwl*R*D1;
    iDx << Matrix<double, """+str(phs.dims.xl)+", "+str(phs.dims.xl)+""">::Identity() * fs - 0.5*tildeA2*Q;
    Dx = iDx.inverse();
    A2 << Dx*tildeA2*Q;
    B2 << Dx*tildeB2;
    C2 << Dx*tildeC2;
    D2 << Dx*tildeD2;
    A3 << Q*(Matrix<double, """+str(phs.dims.xl)+", "+str(phs.dims.xl)+""">::Identity()+0.5*A2);
    B3 << 0.5*Q*B2;
    C3 << 0.5*Q*C2;
    D3 << 0.5*Q*D2;"""
    else:
        str_mat_xl = ""

    if phs.dims.xl > 0 and phs.dims.wl > 0:
        str_A7 = "\n    A7 << A2, A6 ;"
    elif phs.dims.xl > 0 and phs.dims.wl == 0:
        str_A7 = "\n    A7 << A2 ;"
    elif phs.dims.xl == 0 and phs.dims.wl > 0:
        str_A7 = "\n    A7 << A6 ;"
    elif phs.dims.xl == 0 and phs.dims.wl == 0:
        str_A7 = ""

    if phs.dims.xnl() > 0:
        if phs.dims.xl > 0 and phs.dims.wl > 0:
            str_B7 = "\n    B7 << B2, B6 ;"
        elif phs.dims.xl > 0 and phs.dims.wl == 0:
            str_B7 = "\n    B7 << B2 ;"
        elif phs.dims.xl == 0 and phs.dims.wl > 0:
            str_B7 = "\n    B7 << B6 ;"
        elif phs.dims.xl == 0 and phs.dims.wl == 0:
            str_B7 = ""
        if phs.dims.wnl() > 0:
            str_Bxnl = "\n    Bxnl << B4, C4;"
        elif phs.dims.wnl() == 0:
            str_Bxnl = "\n    Bxnl << B4;"
    elif phs.dims.xnl() == 0:
        str_B7 = ""
        str_Bxnl = ""

    if phs.dims.wnl() > 0:
        if phs.dims.xl > 0 and phs.dims.wl > 0:
            str_C7 = "\n    C7 << C2, C6 ;"
        elif phs.dims.xl > 0 and phs.dims.wl == 0:
            str_C7 = "\n    C7 << C2 ;"
        elif phs.dims.xl == 0 and phs.dims.wl > 0:
            str_C7 = "\n    C7 << C6 ;"
        elif phs.dims.xl == 0 and phs.dims.wl == 0:
            str_C7 = ""
        if phs.dims.xnl() > 0:
            str_Bwnl = "\n    Bwnl << B5, C5;"
        elif phs.dims.xnl() == 0:
            str_Bwnl = "\n    Bwnl << C5;"
    elif phs.dims.wnl() == 0:
        str_C7 = ""
        str_Bwnl = ""

    if phs.dims.y() > 0:
        if phs.dims.xl > 0 and phs.dims.wl > 0:
            str_D7 = "\n    D7 << D2, D6 ;"
        elif phs.dims.xl > 0 and phs.dims.wl == 0:
            str_D7 = "\n    D7 << D2 ;"
        elif phs.dims.xl == 0 and phs.dims.wl > 0:
            str_D7 = "\n    D7 << D6 ;"
        elif phs.dims.xl == 0 and phs.dims.wl == 0:
            str_D7 = ""
    elif phs.dims.xnl() == 0:
        str_D7 = ""

    phs_label = phs.label.upper()
    str_process = "void "+phs_label+"::process(vector<double>& In, vector<double>& parameters) {\n "+\
    """
set_u(In);
p = parameters;
UpDate_Matrices();
    """ + str_newton_solver + \
    """
UpDate_l();
UpDate_dxH();
UpDate_z();
UpDate_y();
x += dx;\n}\n"""

    str_process += "void "+phs_label+"::UpDate_Matrices() {\n "
    names = ('xl', 'xnl', 'wl', 'wnl', 'y')
    for namei in names :
        for namej in names:
            str_process += '    UpDate_J' + namei + namej + '();\n';
    str_process += \
        """
    UpDate_R();
    UpDate_Q();
    """ + str_mat_wl + str_mat_xl +\
        """
    tildeA4 << Jxnlxl + Jxnlwl*R*A1;
    tildeB4 << Jxnlxnl + Jxnlwl*R*B1;
    tildeC4 << Jxnlwnl + Jxnlwl*R*C1;
    tildeD4 << Jxnly + Jxnlwl*R*D1;
    A4 << tildeA4*A3;
    B4 << tildeB4+tildeA4*B3;
    C4 << tildeC4+tildeA4*C3;
    D4 << tildeD4+tildeA4*D3;
    tildeA5 << Jwnlxl + Jwnlwl*R*A1;
    tildeB5 << Jwnlxnl + Jwnlwl*R*B1;
    tildeC5 << Jwnlwnl + Jwnlwl*R*C1;
    tildeD5 << Jwnly + Jwnlwl*R*D1;

    A5 << tildeA5*A3;
    B5 << (tildeB5+tildeA5*B3);
    C5 << (tildeC5+tildeA5*C3);
    D5 << (tildeD5+tildeA5*D3);

    A6 << A1*A3;
    B6 << (B1+A1*B3);
    C6 << (C1+A1*C3);
    D6 << (D1+A1*D3);
    """ + str_A7 + str_B7 + str_C7 + str_D7 + str_Bxnl + str_Bwnl + "}\n"
    return str_process


def cfile_full(phs):

    str_includes = '#include "'+ phs.paths['cpp']+"/" + ('phobj').upper() + '.h"\n\n'

    str_variables = """
for(int i=get_nxl(); i<get_nx(); i++){
    dx[i] = 0;
}
for(int i=get_nwl(); i<get_nw(); i++){
    w[i] = 0;
}"""
    str_constructor = "\n// Default Constructor:\n"+class_ref(phs)+phs.label.upper()+"() {\n"+str_variables+"}\n"
    str_initx_constructor = "\n// Constructor Initializing x:\n"+class_ref(phs)+\
                            phs.label.upper()+"(vector<double>& x0) {\n"  +\
                            str_variables+'    if (x.size() == x0.size()) {\n        set_x(x0); \n    }\n    else {\n        cerr << "Size of x0 does not match size of x" << endl;\n        exit(1);\n    }\n}\n'

    str_destructor = "\n// Default Destructor:\n"+class_ref(phs)+ "~"+phs.label.upper()+"() {\n\n}\n"

    str_modificators = "\n// Mutators of private variables\n"
    str_modificators += "void "+class_ref(phs)+"set_u(vector<double> v) {\n        for (int i=0; i<get_ny(); i++) {\n        u[i] = v[i];\n}\n}\n"
    str_modificators += "void "+class_ref(phs)+"set_x(vector<double> v) {\n        for (int i=0; i<get_nx(); i++) {\n        x[i] = v[i];\n}\n}\n"

    str_c = ""
    str_c += str_includes
    str_c += str_constructor
    str_c += str_initx_constructor
    str_c += str_destructor
    str_c += str_process_full(phs)
    str_c += str_accesors_full(phs)
    str_c += str_modificators
    str_c += str_functions_full(phs)
    str_c += str_pointer_full(phs)

    c_file = open(phs.paths['cpp']+"/"+"phobj.cpp", 'w')
    c_file.write(str_c)
    c_file.close()

    return str_c
