import storage
import name

storage.remount("/", readonly=False)

m = storage.getmount("/")
m.label = 'CIRCUITPY{:02X}'.format(name.kBoardId)

storage.remount("/", readonly=True)