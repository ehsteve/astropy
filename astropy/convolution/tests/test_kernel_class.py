# Licensed under a 3-clause BSD style license - see LICENSE.rst
import itertools

import numpy as np
from numpy.testing import assert_almost_equal

from ...tests.helper import pytest
from ..convolve import convolve, convolve_fft
from ..kernels import (
    Gaussian1DKernel, Gaussian2DKernel, Box1DKernel, Box2DKernel,
    Trapezoid1DKernel, TrapezoidDisk2DKernel, MexicanHat1DKernel,
    Tophat2DKernel, MexicanHat2DKernel, AiryDisk2DKernel, Ring2DKernel,
    CustomKernel)

from ..utils import KernelSizeError
from ...modeling.models import Box2DModel

try:
    from scipy.ndimage import filters
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

widths = [3, 5, 7, 9]
modes = ['center', 'linear_interp', 'oversample', 'integrate']
kernel_types = [Gaussian1DKernel, Gaussian2DKernel,
                Box1DKernel, Box2DKernel,
                Trapezoid1DKernel, TrapezoidDisk2DKernel,
                MexicanHat1DKernel, Tophat2DKernel, AiryDisk2DKernel, Ring2DKernel]

# Test data
delta_pulse_1D = np.zeros(81)
delta_pulse_1D[40] = 1

delta_pulse_2D = np.zeros((81, 81))
delta_pulse_2D[40, 40] = 1

random_data_1D = np.random.rand(61)
random_data_2D = np.random.rand(61, 61)


class TestKernels(object):
    """
    Test class for the built-in convolution kernels.
    """

    @pytest.mark.skipif('not HAS_SCIPY')
    @pytest.mark.parametrize(('width'), widths)
    def test_scipy_filter_gaussian(self, width):
        """
        Test GaussianKernel against SciPy ndimage gaussian filter.
        """
        gauss_kernel_1D = Gaussian1DKernel(width)
        gauss_kernel_1D.normalize()
        gauss_kernel_2D = Gaussian2DKernel(width)
        gauss_kernel_2D.normalize()

        astropy_1D = convolve(delta_pulse_1D, gauss_kernel_1D, boundary='fill')
        astropy_2D = convolve(delta_pulse_2D, gauss_kernel_2D, boundary='fill')

        scipy_1D = filters.gaussian_filter(delta_pulse_1D, width)
        scipy_2D = filters.gaussian_filter(delta_pulse_2D, width)

        assert_almost_equal(astropy_1D, scipy_1D, decimal=12)
        assert_almost_equal(astropy_2D, scipy_2D, decimal=12)

    @pytest.mark.skipif('not HAS_SCIPY')
    @pytest.mark.parametrize(('width'), widths)
    def test_scipy_filter_gaussian_laplace(self, width):
        """
        Test MexicanHat kernels against SciPy ndimage gaussian laplace filters.
        """
        mexican_kernel_1D = MexicanHat1DKernel(width)
        mexican_kernel_2D = MexicanHat2DKernel(width)

        astropy_1D = convolve(delta_pulse_1D, mexican_kernel_1D, boundary='fill')
        astropy_2D = convolve(delta_pulse_2D, mexican_kernel_2D, boundary='fill')

        # The Laplace of Gaussian filter is an inverted Mexican Hat
        # filter.
        scipy_1D = -filters.gaussian_laplace(delta_pulse_1D, width)
        scipy_2D = -filters.gaussian_laplace(delta_pulse_2D, width)

        # There is a slight deviation in the normalization. They differ by a
        # factor of ~1.0000284132604045. The reason is not known.
        assert_almost_equal(astropy_1D, scipy_1D, decimal=5)
        assert_almost_equal(astropy_2D, scipy_2D, decimal=5)

    @pytest.mark.parametrize(('kernel_type', 'width'), list(itertools.product(kernel_types, widths)))
    def test_delta_data(self, kernel_type,  width):
        """
        Test smoothing of an image with a single positive pixel
        """
        if kernel_type == AiryDisk2DKernel and not HAS_SCIPY:
            pytest.skip("Omitting AiryDisk2DKernel, which requires SciPy")
        if not kernel_type == Ring2DKernel:
            kernel = kernel_type(width)
        else:
            kernel = kernel_type(width, width * 0.2)

        if kernel.dimension == 1:
            c1 = convolve_fft(delta_pulse_1D, kernel, boundary='fill')
            c2 = convolve(delta_pulse_1D, kernel, boundary='fill')
            assert_almost_equal(c1, c2, decimal=12)
        else:
            c1 = convolve_fft(delta_pulse_2D, kernel, boundary='fill')
            c2 = convolve(delta_pulse_2D, kernel, boundary='fill')
            assert_almost_equal(c1, c2, decimal=12)

    @pytest.mark.parametrize(('kernel_type', 'width'), list(itertools.product(kernel_types, widths)))
    def test_random_data(self, kernel_type, width):
        """
        Test smoothing of an image made of random noise
        """
        if kernel_type == AiryDisk2DKernel and not HAS_SCIPY:
            pytest.skip("Omitting AiryDisk2DKernel, which requires SciPy")
        if not kernel_type == Ring2DKernel:
            kernel = kernel_type(width)
        else:
            kernel = kernel_type(width, width * 0.2)

        if kernel.dimension == 1:
            c1 = convolve_fft(random_data_1D, kernel, boundary='fill')
            c2 = convolve(random_data_1D, kernel, boundary='fill')
            assert_almost_equal(c1, c2, decimal=12)
        else:
            c1 = convolve_fft(random_data_2D, kernel, boundary='fill')
            c2 = convolve(random_data_2D, kernel, boundary='fill')
            assert_almost_equal(c1, c2, decimal=12)

    @pytest.mark.parametrize(('width'), widths)
    def test_uniform_smallkernel(self, width):
        """
        Test smoothing of an image with a single positive pixel

        Instead of using kernel class, uses a simple, small kernel
        """
        kernel = np.ones([width, width])

        c2 = convolve_fft(delta_pulse_2D, kernel, boundary='fill')
        c1 = convolve(delta_pulse_2D, kernel, boundary='fill')
        assert_almost_equal(c1, c2, decimal=12)

    @pytest.mark.parametrize(('width'), widths)
    def test_smallkernel_vs_Box2DKernel(self, width):
        """
        Test smoothing of an image with a single positive pixel
        """
        kernel1 = np.ones([width, width]) / width ** 2
        kernel2 = Box2DKernel(width)

        c2 = convolve_fft(delta_pulse_2D, kernel2, boundary='fill')
        c1 = convolve_fft(delta_pulse_2D, kernel1, boundary='fill')

        assert_almost_equal(c1, c2, decimal=12)

    def test_convolve_1D_kernels(self):
        """
        Check if convolving two kernels with eachother works correctly.
        """
        gauss_1 = Gaussian1DKernel(3)
        gauss_2 = Gaussian1DKernel(4)
        test_gauss_3 = Gaussian1DKernel(5)

        gauss_3 = convolve(gauss_1, gauss_2)
        assert np.all(np.abs((gauss_3 - test_gauss_3).array) < 0.01)

    def test_convolve_2D_kernels(self):
        """
        Check if convolving two kernels with eachother works correctly.
        """
        gauss_1 = Gaussian2DKernel(3)
        gauss_2 = Gaussian2DKernel(4)
        test_gauss_3 = Gaussian2DKernel(5)

        gauss_3 = convolve(gauss_1, gauss_2)
        assert np.all(np.abs((gauss_3 - test_gauss_3).array) < 0.01)

    def test_multiply_scalar(self):
        """
        Check if multiplying two kernels with eachother works correctly.
        """
        gauss = 1 * Gaussian1DKernel(3)
        assert np.all(np.abs(3 * gauss.array - gauss * 3) < 0.000001)

    def test_custom_1D_kernel(self):
        """
        Check if CustomKernel against Box1DKernel.
        """
        #Define one dimensional array:
        array = np.ones(5)
        custom = CustomKernel(array)
        custom.normalize()
        box = Box1DKernel(5)

        c2 = convolve(delta_pulse_1D, custom, boundary='fill')
        c1 = convolve(delta_pulse_1D, box, boundary='fill')
        assert_almost_equal(c1, c2, decimal=12)

    def test_custom_2D_kernel(self):
        """
        Check if CustomKernel against Box1DKernel.
        """
        #Define one dimensional array:
        array = np.ones((5, 5))
        custom = CustomKernel(array)
        custom.normalize()
        box = Box2DKernel(5)

        c2 = convolve(delta_pulse_2D, custom, boundary='fill')
        c1 = convolve(delta_pulse_2D, box, boundary='fill')
        assert_almost_equal(c1, c2, decimal=12)

    def test_custom_1D_kernel_list(self):
        """
        Check if CustomKernel works with lists.
        """
        custom = CustomKernel([1, 1, 1, 1, 1])
        assert custom.is_bool == True

    def test_custom_2D_kernel_list(self):
        """
        Check if CustomKernel works with lists.
        """
        custom = CustomKernel([[1, 1, 1],
                               [1, 1, 1],
                               [1, 1, 1]])
        assert custom.is_bool == True

    def test_custom_kernel_odd_error(self):
        """
        Check if CustomKErnel raises if the array size is odd.
        """
        with pytest.raises(KernelSizeError):
            custom = CustomKernel([1, 1, 1, 1])

    def test_add_1D_kernels(self):
        """
        Check if adding of two 1D kernels works.
        """
        box_1 = Box1DKernel(5)
        box_2 = Box1DKernel(3)
        box_3 = Box1DKernel(1)
        box_sum = box_1 + box_2 + box_3
        ref = [1/5., 1/5. + 1/3., 1 + 1/3. + 1/5., 1/5. + 1/3., 1/5.]
        assert_almost_equal(box_sum.array, ref, decimal=12)

    def test_add_2D_kernels(self):
        """
        Check if adding of two 1D kernels works.
        """
        box_1 = Box2DKernel(3)
        box_2 = Box2DKernel(1)
        box_sum = box_1 + box_2
        ref = [[1 / 9., 1 / 9., 1 / 9.],
               [1 / 9., 1 + 1 / 9., 1 / 9.],
               [1 / 9., 1 / 9., 1 / 9.]]
        assert_almost_equal(box_sum.array, ref, decimal=12)

    def test_Gaussian1DKernel_even_size(self):
        """
        Check if even size for GaussianKernel works.
        """
        gauss = Gaussian1DKernel(3, x_size=10)
        assert gauss.array.size == 10

    def test_Gaussian2DKernel_even_size(self):
        """
        Check if even size for GaussianKernel works.
        """
        gauss = Gaussian2DKernel(3, x_size=10, y_size=10)
        assert gauss.array.shape == (10, 10)

    def test_normalize_peak(self):
        """
        Check if normalize works with peak mode.
        """
        custom = CustomKernel([1, 2, 3, 2, 1])
        custom.normalize(mode='peak')
        assert custom.array.max() == 1

    def test_check_kernel_attributes(self):
        """
        Check if kernel attributes are correct.
        """
        box = Box2DKernel(5)

        # Check truncation
        assert box.truncation == 0

        # Check model
        assert isinstance(box.model, Box2DModel)

        # Check center
        assert box.center == [2, 2]

        # Check normalization
        assert_almost_equal(box.normalization, 1., decimal=12)

        # Check seperability
        assert box.separable

    @pytest.mark.parametrize(('kernel_type', 'mode'), list(itertools.product(kernel_types, modes)))
    def test_dicretize_modes(self, kernel_type, mode):
        """
        Check if the different modes result in kernels that work with convolve.
        Use only small kernel width, to make the test pass quickly.
        """
        if kernel_type == AiryDisk2DKernel and not HAS_SCIPY:
            pytest.skip("Omitting AiryDisk2DKernel, which requires SciPy")
        if not kernel_type == Ring2DKernel:
            kernel = kernel_type(3)
        else:
            kernel = kernel_type(3, 3 * 0.2)

        if kernel.dimension == 1:
            c1 = convolve_fft(delta_pulse_1D, kernel, boundary='fill')
            c2 = convolve(delta_pulse_1D, kernel, boundary='fill')
            assert_almost_equal(c1, c2, decimal=12)
        else:
            c1 = convolve_fft(delta_pulse_2D, kernel, boundary='fill')
            c2 = convolve(delta_pulse_2D, kernel, boundary='fill')
            assert_almost_equal(c1, c2, decimal=12)


