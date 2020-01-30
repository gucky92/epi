""" General util functions for EPI. """

import numpy as np
import tensorflow as tf
import pickle
import os
from epi.error_formatters import format_type_err_msg


def gaussian_backward_mapping(mu, Sigma):
    if type(mu) is not np.ndarray:
        raise TypeError(
            format_type_err_msg(
                "epi.util.gaussian_backward_mapping", "mu", mu, np.ndarray
            )
        )
    elif type(Sigma) is not np.ndarray:
        raise TypeError(
            format_type_err_msg(
                "epi.util.gaussian_backward_mapping", "Sigma", Sigma, np.ndarray
            )
        )

    mu = np_column_vec(mu)
    Sigma_shape = Sigma.shape
    if len(Sigma_shape) != 2:
        raise ValueError("Sigma must be 2D matrix, shape ", Sigma_shape, ".")
    if Sigma_shape[0] != Sigma_shape[1]:
        raise ValueError("Sigma must be square matrix, shape ", Sigma_shape, ".")
    if not np.allclose(Sigma, Sigma.T, atol=1e-10):
        raise ValueError("Sigma must be symmetric. shape.")
    if Sigma_shape[1] != mu.shape[0]:
        raise ValueError("mu and Sigma must have same dimensionality.")

    D = mu.shape[0]
    Sigma_inv = np.linalg.inv(Sigma)
    x = np.dot(Sigma_inv, mu)
    y = np.reshape(-0.5 * Sigma_inv, (D ** 2))
    eta = np.concatenate((x[:, 0], y), axis=0)
    return eta


def np_column_vec(x):
    """ Takes numpy vector and orients it as a n x 1 column vec. 

    :param x: Vector of length n
    :type x: class:`np.ndarray`
    :return: n x 1 numpy column vector
    :rtype: class:`numpy.ndarray`
    """
    if type(x) is not np.ndarray:
        raise (
            TypeError(format_type_err_msg("epi.util.np_column_vec", "x", x, np.ndarray))
        )
    x_shape = x.shape
    if len(x_shape) == 1:
        x = np.expand_dims(x, 1)
    elif len(x_shape) == 2:
        if x_shape[1] != 1:
            if x_shape[0] > 1:
                raise ValueError("x is matrix.")
            else:
                x = x.T
    elif len(x_shape) > 2:
        raise ValueError("x dimensions > 2.")
    return x


def array_str(a):
    """Returns a compressed string from a 1-D numpy array.

    :param a: A 1-D numpy array.
    :type a: str
    :return: A string compressed via scientific notation and repeated elements.
    :rtype: str
    """
    if type(a) is not np.ndarray:
        raise TypeError(format_type_err_msg("epi.util.array_str", "a", a, np.ndarray))

    if len(a.shape) > 1:
        raise ValueError("epi.util.array_str takes 1-D arrays not %d." % len(a.shape))

    def repeats_str(num, mult):
        if mult == 1:
            return "%.2E" % num
        else:
            return "%dx%.2E" % (mult, num)

    d = a.shape[0]
    mults = []
    nums = []
    prev_num = a[0]
    mult = 1
    for i in range(1, d):
        if a[i] == prev_num:
            mult += 1
        else:
            nums.append(prev_num)
            prev_num = a[i]
            mults.append(mult)
            mult = 1

        if i == d - 1:
            nums.append(prev_num)
            mults.append(mult)

    array_str = repeats_str(nums[0], mults[0])
    for i in range(1, len(nums)):
        array_str += "_" + repeats_str(nums[i], mults[i])

    return array_str


def init_path(arch_string, init_type, init_param):
    """Deduces initialization file path from initialization type and parameters.

    :param arch_string: Architecture string of normalizing flow.
    :type arch_string: str
    :param init_type: Initialization type \in ['iso_gauss']
    :type init_type: str
    :param init_param: init_type dependent parameters for initialization (more deets)
    :type dict: 

    :return: Initialization save path.
    :rtype: str
    """
    if type(arch_string) is not str:
        raise TypeError(
            format_type_err_msg("epi.util.init_path", "arch_string", arch_string, str)
        )
    if type(init_type) is not str:
        raise TypeError(
            format_type_err_msg("epi.util.init_path", "init_type", init_type, str)
        )

    path = "./data/" + arch_string + "/"
    if not os.path.exists(path):
        os.makedirs(path)

    if init_type == "iso_gauss":
        if "loc" in init_param:
            loc = init_param["loc"]
        else:
            raise ValueError("'loc' field not in init_param for %s." % init_type)
        if "scale" in init_param:
            scale = init_param["scale"]
        else:
            raise ValueError("'scale' field not in init_param for %s." % init_type)
        path += init_type + "_loc=%.2E_scale=%.2E" % (loc, scale)

    return path


def save_tf_model(path, variables):
    """Saves tensorflow model variables via pickle to file at path.

    :param path: Path to file for saving model variables.
    :type path: str
    :param variables: List of tensorflow model variables to be saved.
    :type variables: list
    """
    if (type(path) is not str):
        raise TypeError(format_type_err_msg("epi.util.save_tf_model", "path", path, str))
    if (type(variables) is not list):
        raise TypeError(format_type_err_msg("epi.util.save_tf_model", "variables", variables, list))
    if (len(variables) == 0):
        raise ValueError("epi.util.save_tf_model must receive nonempty list of variables.")

    d = {}
    for variable in variables:
        d[variable.name] = variable.numpy()
    pickle.dump(d, open(path + ".p", "wb"))
    return None


def load_tf_model(path, variables):
    """Loads tensorflow model variables via pickle from file at path.

    :param path: Path to file with saved model variables.
    :type path: str
    :param variables: List of tensorflow model variables to assign values.
    :type variables: list
    """
    if (type(path) is not str):
        raise TypeError(format_type_err_msg("epi.util.save_tf_model", "path", path, str))
    if (type(variables) is not list):
        raise TypeError(format_type_err_msg("epi.util.save_tf_model", "variables", variables, list))
    if (len(variables) == 0):
        raise ValueError("epi.util.save_tf_model must receive nonempty list of variables.")

    filename = path + ".p"
    if (not os.path.exists(filename)):
        raise ValueError("Filename %s does not exist." % filename)

    d = pickle.load(open(filename, "rb"))
    for variable in variables:
        if (variable.name not in d):
            raise ValueError("Variable %s not in file %s." % (variable.name, filename))
        variable.assign(d[variable.name])
    return None
