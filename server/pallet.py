#import matplotlib.pyplot as plt

from configuration import ItemType
#from utils import list_pose,pose_list


def list_pose(l):
  assert type(l) is list
  return {'x' : l[0], 'y' : l[1], 'z' : l[2], 'rx' : l[3], 'ry' : l[4], 'rz' : l[5]}

def pose_list(p):
  assert type(p) is dict
  return [p['x'], p['y'], p['z'], p['rx'], p['ry'], p['rz']]
waypoints= {}

class Pallet:
    def __init__(self, wps, rows, cols):
        self.wp1, self.wp2, self.wp3, self.rows, self.cols = wps[0], wps[1], wps[2], rows, cols
        self.pallet_coordinates = self.generate_pallet_coordinates()
        self.pallet_coordinates_flat = [point for row in self.pallet_coordinates for point in row]

    def calculate_increments(self, start_point, end_point, divisions):
        # Calculate the step increments in x and y directions between two points for a given number of divisions.
        x_step = (end_point['x'] - start_point['x']) / (divisions - 1) if divisions > 1 else 0
        y_step = (end_point['y'] - start_point['y']) / (divisions - 1) if divisions > 1 else 0
        return x_step, y_step

    def generate_pallet_coordinates(self):
        # Calculate row-wise and column-wise increments
        col_x_step, col_y_step = self.calculate_increments(self.wp1, self.wp2, self.cols)  # For horizontal axis (columns)
        row_x_step, row_y_step = self.calculate_increments(self.wp1, self.wp3, self.rows)  # For vertical axis (rows)
        pallet_coordinates = []
        # Generate the pallet of coordinates row by row
        for row in range(self.rows):
            row_coordinates = []
            for col in range(self.cols):
                x = self.wp1['x'] + col * col_x_step + row * row_x_step
                y = self.wp1['y'] + col * col_y_step + row * row_y_step
                row_coordinates.append(list_pose([x, y, self.wp1['z'], self.wp1['rx'],self.wp1['ry'],self.wp1['rz']]))
            pallet_coordinates.append(row_coordinates)
        return pallet_coordinates

    def get_coordinates_as_list(self):
        # Flatten the pallet coordinates into a single list of (x, y) points.
        return [point for row in self.pallet_coordinates for point in row]
    
    def get_coordinate_with_index(self, index):
        return list_pose([self.pallet_coordinates_flat[index-1]['x'], self.pallet_coordinates_flat[index-1]['y'], self.wp1['z'], self.wp1['rx'],self.wp1['ry'],self.wp1['rz']])

    # def plot_pallet(self):
    #     # Plot the pallet in Cartesian space.
    #     flat_coords = self.get_coordinates_as_list()
    #     x_coords = [point[0] for point in flat_coords]
    #     y_coords = [point[1] for point in flat_coords]
        
    #     plt.scatter(x_coords, y_coords)
    #     plt.xlabel('X')
    #     plt.ylabel('Y')
    #     plt.title('Generated 2D pallet of Coordinates')
    #     plt.show()


class PalletList:
    def __init__(self, wps, list_rows, list_cols, pallet_rows, pallet_cols):
        self.wp1, self.wp2, self.wp3, self.wp4, self.wp5 = wps[0], wps[1], wps[2], wps[3], wps[4]
        self.list_rows, self.list_cols, self.pallet_rows, self.pallet_cols = list_rows, list_cols, pallet_rows, pallet_cols
        self.palletList = Pallet([self.wp1, self.wp2, self.wp3], self.list_rows, self.list_cols)
        self.pallet = Pallet([self.wp1, self.wp4, self.wp5], self.pallet_rows, self.pallet_cols)

    def get_coordinates_as_list(self):
        m_coordinates = []
        for m in range(self.list_rows*self.list_cols):
            p_coordinates = []
            for p in range(self.pallet_rows*self.pallet_cols):
                m_wp = self.palletList.get_coordinate_with_index(m+1)
                p_wp = self.pallet.get_coordinate_with_index(p+1)
                x = m_wp['x']+(p_wp['x']-self.wp1['x'])
                y = m_wp['y']+(p_wp['y']-self.wp1['y'])
                p_coordinates.append(list_pose([x,y, self.wp1['z'], self.wp1['rx'],self.wp1['ry'],self.wp1['rz']]))
            m_coordinates.extend(p_coordinates)
        return m_coordinates
    
    # def plot_pallet(self):
    #     # Plot the pallet in Cartesian space.
    #     flat_coords = self.get_coordinates_as_list()
    #     x_coords = [point[0] for point in flat_coords]
    #     y_coords = [point[1] for point in flat_coords]
        
    #     plt.scatter(x_coords, y_coords)
    #     plt.xlabel('X')
    #     plt.ylabel('Y')
    #     plt.title('Generated 2D pallet of Coordinates')
    #     plt.show()


def main():
    # Example: Define 3 points in Cartesian coordinates and the size of the pallet
    wp1 = [2, 2, 50, 0, 0, 0]  # Top-left
    wp2 = [6, 2, 50, 0, 0, 0]  # Top-right
    wp3 = [2, 6, 50, 0, 0, 0]  # Bottom-left
    mrows = 2  # Number of rows
    mcols = 2  # Number of columns
    wp4 = [5, 2, 50, 0, 0, 0]  # Top-right
    wp5 = [2, 5, 50, 0, 0, 0]  # Bottom-left
    rows = 2  # Number of rows
    cols = 2  # Number of columns

    # Create the pallet
    pallet = PalletList([list_pose(wp1), list_pose(wp2), list_pose(wp3), list_pose(wp4), list_pose(wp5)], mrows, mcols, rows, cols)
    print(pallet.get_coordinates_as_list())
    pallet.plot_pallet()

#main()

def poses_to_Lists(points):
    poses:list=[]
    for point in points:
        poses.append(pose_list(point))
    return poses

def calculate_waypoints(points,p_rows,p_columns,ch_rows=0,ch_columns=0,pallets=None):
    if pallets:
        if len(points) == 9:
            result= []
            pallet1= Pallet(points[:3],pallets[0]['rows'],pallets[0]['cols'])
            result.extend(pallet1.get_coordinates_as_list())
            pallet2= Pallet(points[3:6],pallets[1]['rows'],pallets[1]['cols'])
            result.extend(pallet2.get_coordinates_as_list())
            pallet3= Pallet(points[-3:],pallets[2]['rows'],pallets[2]['cols'])
            result.extend(pallet3.get_coordinates_as_list())
            return result
    else:
        if len(points) == 5:
            pallet=PalletList(points,p_rows,p_columns,ch_rows,ch_columns)
            return pallet.get_coordinates_as_list()
        elif len(points) == 3:
            pallet=Pallet(points,p_rows,p_columns)
            return pallet.get_coordinates_as_list()
        elif len(points) == 9: # fridges or archive racks
            result= []
            pallet1= Pallet(points[:3],p_rows,p_columns)
            result.extend(pallet1.get_coordinates_as_list())
            pallet2= Pallet(points[3:6],p_rows,p_columns)
            result.extend(pallet2.get_coordinates_as_list())
            pallet3= Pallet(points[-3:],p_rows,p_columns)
            result.extend(pallet3.get_coordinates_as_list())
            return result
        elif len(points) == 6: # dxci racks
            result= []
            pallet1= Pallet(points[:3],int(p_rows/2),p_columns)
            result.extend(pallet1.get_coordinates_as_list())
            pallet2= Pallet(points[3:6],int(p_rows/2),p_columns)
            result.extend(pallet2.get_coordinates_as_list())
            return result
        
        elif len(points) == 4: # ortho machine racks
            result= []
            for i in range(6):
                result.extend(points)
            return result
    return points

def get_waypoints(position,zone_id,subzone_id=0,type=ItemType.VIAL.value,robot_id=1):
    try:
        waypnts=waypoints.get((robot_id,zone_id,subzone_id,type))
        if waypnts:
            return waypnts[position-1]
        return list_pose([0,0,0,0,0,0])
    except Exception as e: 
        print(e)
