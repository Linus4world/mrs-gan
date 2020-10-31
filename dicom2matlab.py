from options.dicom2matlab_options import Dicom2MatlabOptions
import numpy as np
import scipy.io as io
from util.util import progressbar, is_set_of_type
from util.load_activated_spectra import *
from data.image_folder import make_dataset
from util.process_spectra import preprocess_numpy_spectra

opt = Dicom2MatlabOptions().parse()

def extract_from_DCM(sourceDir: str, file_name_spec: str, file_ext_metabolite:str, metabolites: list, save_dir):
    spectra_paths = sorted(make_dataset(sourceDir, file_ext=file_name_spec))
    print('Number of patients:', len(spectra_paths))
    metabolite_paths = {}
    for metabolite in metabolites:
        metabolite_paths[metabolite] = sorted(make_dataset(sourceDir, file_ext=file_ext_metabolite + metabolite + '.dcm'))
    assert len(metabolite_paths) == len(metabolites)

    spectra_real = []
    spectra_imag = []
    quantities = {k: [] for k in metabolites}
    for i in progressbar(range(len(spectra_paths)), "Processing patient data: ", 20):
        metabolic_map_path = metabolite_paths[metabolites[0]][i]
        activated_indices, shape = get_activated_indices(metabolic_map_path)
        dataR, dataI = get_activated_spectra(spectra_paths[i], activated_indices, shape)
        spectra_real.append(dataR)
        spectra_imag.append(dataI)
        for metabolite, paths in metabolite_paths.items():
            quantities[metabolite].append(get_activated_metabolite_values(paths[i], activated_indices, shape))

    spectra_real = np.concatenate(spectra_real, axis=0)
    spectra_imag = np.concatenate(spectra_imag, axis=0)

    for metabolite in metabolites:
        quantities[metabolite] = np.concatenate(quantities[metabolite], axis=0)

    spectra = preprocess_numpy_spectra(spectra_real, spectra_imag, spectra_real.shape, save_dir, opt)
    spectra = spectra.transpose(1, 2)
    return spectra, quantities

# def convert_DCM_to_MAT_NUMPY(sourceDir: str, file_ext_A: str, file_ext_B: str):
#     """
#     Loads the dicom encoded spectra and their respective metabolic maps, selects spectra of the activated voxels and stores them in a .npz and a .mat file
#     """

#     # Implementing Matlab code from UCSF
#     # Compile loaded, reshaped data in row-wise matrix
#     A_paths = sorted(make_dataset(sourceDir, file_ext=file_ext_A))
#     B_paths = sorted(make_dataset(sourceDir, file_ext=file_ext_B))
#     print('Number of spectra: ' + str(len(A_paths)) + ', Number of metabolic maps: ' + str(len(B_paths)))

#     for i in progressbar(range(len(A_paths)), "Processing patient data: ", 20):
#         # Identify activated voxels using the NAA map and extract corresponding spectra
#         dataR, dataI = get_activated_spectra(B_paths[i], A_paths[i])
#         dataR, dataI = torch.FloatTensor(dataR), torch.FloatTensor(dataI)
#         size = dataR.shape
#         spectra = torch.empty([2, size[0], size[1]])

#         spectra[0,:,:] = dataR
#         spectra[1,:,:] = dataI
#         # Store matlab + numpy file next to dicom files
#         split = os.path.split(A_paths[i])
#         path = os.path.join(split[0], os.path.splitext(split[1])[0])
#         np.savez_compressed(path, data=spectra)
#         io.savemat(path + '.mat', mdict={'spectra': np.array(spectra)})

# def load_from_numpy(source_dir, save_dir):
#     """
#     Load samples from numpy files and perform preprocessing.
#     Returns all spectra as a numpy array of size
#     NUM_SAMPLES x 2 x SPECTRA_LENGTH
#     """
#     spectraR = []
#     spectraI = []
#     L = []

#     A_paths = make_dataset(source_dir, file_type='numpy') # Returns a list of paths of the files in the dataset
#     A_paths = sorted(A_paths)
#     for i in progressbar(range(len(A_paths)), "Loading patient data: ", 20):
#         datar, datai = np.load(A_paths[i]).get('data')
#         spectraR.append(datar)
#         spectraI.append(datai)
#         L.append(len(spectraR[i]))
#     spectraR = np.concatenate(spectraR, axis=0)
#     spectraI = np.concatenate(spectraI, axis=0)
    
#     spectra = preprocess_numpy_spectra(spectraR, spectraI, spectraR.shape, save_dir, opt)
#     spectra = spectra.transpose(1, 2)
#     return spectra

def export_mat(mat_dict, path):
    """ Saves the given dictionary as a matlab file at the given path"""
    io.savemat(path + '.mat', mdict=mat_dict)

def dcm2mat(source_dir, save_dir):
    """
    This function loads all DICOM files from all subfolders at the given path and stores all spectra and quantities in two seperate matlab files.
    The variable holding the spectra is called 'spectra'.
    The data is transformed like this:
    """
    if not is_set_of_type(source_dir, '.dcm'):
        raise ValueError("Source directory does not contain any valid spectra")

    spectra, quantities = extract_from_DCM(source_dir, opt.file_ext_spectra, opt.file_ext_metabolite, ['cre', 'cho', 'NAA'], opt.save_dir)
    
    if opt.real:
        name = 'spectra_real'
    elif opt.imag:
        name = 'spectra_imag'
    elif opt.mag:
        name = 'spectra_magnitude'
    else:
        name = 'spectra'
    export_mat({'spectra': np.array(spectra)}, opt.save_dir + name)
    export_mat(quantities, save_dir + 'quantities')

dcm2mat(opt.source_dir,  opt.save_dir)