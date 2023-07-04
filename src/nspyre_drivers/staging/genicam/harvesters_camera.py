"""
Driver for generic GenICam compliant cameras.

See https://harvesters.readthedocs.io/en/latest/TUTORIAL.html#workflow-overview.

Copyright (c) 2023, Jacob Feder
All rights reserved.
"""

from harvesters.core import Harvester
from harvesters.util.pfnc import mono_location_formats
from harvesters.util.pfnc import rgb_formats
from harvesters.util.pfnc import bgr_formats
from harvesters.util.pfnc import rgba_formats
from harvesters.util.pfnc import bgra_formats

class HarvestersCamera:
    """Harvesters-based camera wrapper driver."""
    def __init__(self, cti_file):
        """
        Args:
            cti_file: TODO
            vendor: TODO
            serial_number: TODO
        """
        self.cti_file = cti_file

        self.harvester = Harvester()
        self.ia = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def connect(self):
        """TODO"""
        self.harvester.__enter__()
        # device description file
        self.harvester.add_file(self.cti_file)
        # update the harvester with the new cti
        self.harvester.update()
        # image acquirer
        self.ia = self.harvester.create()
        self.ia.__enter__()

    def disconnect(self):
        """TODO"""
        if self.ia is not None:
            self.ia.__exit__(None, None, None)
        self.harvester.__exit__(None, None, None)

    def start_acquisition(self):
        """TODO"""
        if self.ia is not None:
            self.ia.start()
        else:
            raise RuntimeError('Camera is not connected.')

    def stop_acquisition(self):
        """TODO"""
        if self.ia is not None:
            self.ia.stop()
        else:
            raise RuntimeError('Camera is not connected.')

    def features(self):
        """TODO"""
        return dir(self.ia.device.node_map)

    def get_frame(self):
        """TODO"""
        with self.ia.fetch() as buffer:
            component = buffer.payload.components[0]
            width = component.width
            height = component.height
            data_format = component.data_format

            # reshape the image:
            if data_format in mono_location_formats:
                image = component.data.reshape(height, width)
            elif data_format in rgb_formats or \
                data_format in rgba_formats or \
                data_format in bgr_formats or \
                data_format in bgra_formats:

                image = component.data.reshape(
                    height,
                    width,
                    int(component.num_components_per_pixel) # Set of R, G, B, and Alpha
                )

                if data_format in bgr_formats:
                    # Swap every R and B:
                    image = image[:, :, ::-1]
            else:
                raise ValueError(f'Data format [{data_format}] not supported.')

            return image

# with Harvesters(
#     cti_file='/opt/VimbaX_2023-1/cti/VimbaUSBTL.cti',
#     vendor='Allied Vision',
#     serial_number='03VGZ'
# ) as cam:
#     cam.start_acquisition()
#     import pdb; pdb.set_trace()
#     print(cam.features())
#     frame = cam.get_frame()
#     cam.stop_acquisition()



# with Harvester() as harvester:
#     # device description file
#     harvester.add_cti_file('/opt/VimbaX_2023-1/cti/VimbaUSBTL.cti')
#     # update the harvester with the new cti
#     harvester.update_device_info_list()
#     # image acquirer
#     # ia = h.create_image_acquirer(vendor='Allied Vision', serial_number='03VGZ')
#     with harvester.create_image_acquirer() as ia:
#         # start acquiring images
#         ia.start_image_acquisition()
#         # fetch an image
#         with ia.fetch_buffer() as buffer:
#             component = buffer.payload.components[0]
#             width = component.width
#             height = component.height
#             data_format = component.data_format

#             # reshape the image:
#             if data_format in mono_location_formats:
#                 image = component.data.reshape(height, width)
#             elif data_format in rgb_formats or \
#                 data_format in rgba_formats or \
#                 data_format in bgr_formats or \
#                 data_format in bgra_formats:

#                 image = component.data.reshape(
#                     height,
#                     width,
#                     int(component.num_components_per_pixel) # Set of R, G, B, and Alpha
#                 )

#                 if data_format in bgr_formats:
#                     # Swap every R and B:
#                     image = image[:, :, ::-1]
#             else:
#                 raise ValueError(f'Data format [{data_format}] not supported.')

#             print(image)
#         # stop acquiring images
#         ia.stop_image_acquisition()
