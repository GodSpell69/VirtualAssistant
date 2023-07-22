import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread
import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingOpenGL2 import (
    vtkOpenGLPolyDataMapper,
    vtkOpenGLActor
    )
from resources.web.threads import *

class MainWindow(QWidget):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.IDesign()
        self.IRecord()
        self.IAnimate()

    def IDesign(self):
        FirstobjPath = r"D:\Gab\prog\Nicole_project\resources\models\brain.obj"
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(300, 500)
        self.move(150, 200)

        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vtkWidget.setFixedSize(300, 500)
        self.reader = vtk.vtkOBJReader()
        self.reader.SetFileName(FirstobjPath)
        self.reader.Update()
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground([0.07, 0.07, 0.07])
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.mapper = vtkOpenGLPolyDataMapper()
        if vtk.VTK_MAJOR_VERSION <= 5:
            self.mapper.SetInput(self.reader.GetOutput())
        else:
            self.mapper.SetInputConnection(self.reader.GetOutputPort())
        self.actor = vtkOpenGLActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetRepresentationToPoints()
        self.actor.SetOrigin(-0.7230189442634583, 1.5103785395622253, 0.8213195204734802)
        self.shaders = self.actor.GetShaderProperty()
        self.iTimeValue = 0.1
        self.shaders.GetFragmentCustomUniforms().SetUniformf("iTime", 0.1)
        self.shaders.GetFragmentCustomUniforms().SetUniform3f("Color", [0.12,0.56,1])
        vec1 = '''//VTK::Normal::Dec
        varying vec3 myNormalMCVSOutput;
        '''
        vec2 = '''//VTK::Normal::Impl
        myNormalMCVSOutput = normalMC;
        '''
        frag1 = '''//VTK::Normal::Dec
        varying vec3 myNormalMCVSOutput;
        '''
        frag2 = '''//VTK::Normal::Impl
        diffuseColor = vec3(Color);
        ambientColor = abs(myNormalMCVSOutput*iTime);
        '''
        self.shaders.AddVertexShaderReplacement(
            "//VTK::Normal::Dec", # replace the normal block
            True, # before the standard replacements
            vec1,
            #"gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;\n", #but we add this
            False # only do it once
        )
        self.shaders.AddVertexShaderReplacement(
            "//VTK::Normal::Impl", # replace the normal block
            True, # before the standard replacements
            vec2,
            False # only do it once
        )
        self.shaders.AddFragmentShaderReplacement(
            "//VTK::Normal::Dec", # replace the normal block
            True, # before the standard replacements
            frag1,
            False # only do it once
        )
        self.shaders.AddFragmentShaderReplacement(
            "//VTK::Normal::Impl", # replace the normal block
            True, # before the standard replacements
            frag2,
            False # only do it once
        )
        self.ren.AddActor(self.actor)
        self.ren.ResetCamera()
        self.camera = self.ren.GetActiveCamera()
        self.camera.Zoom(0.75)
        self.iren.RemoveObservers(vtk.vtkCommand.LeftButtonPressEvent)
        self.iren.RemoveObservers(vtk.vtkCommand.RightButtonPressEvent)
        self.iren.RemoveObservers(vtk.vtkCommand.MiddleButtonPressEvent)
        self.iren.RemoveObservers(vtk.vtkCommand.MouseWheelForwardEvent)
        self.iren.RemoveObservers(vtk.vtkCommand.MouseWheelBackwardEvent)
        self.refresh_rate = 60
        self.iren.CreateRepeatingTimer(int(1/self.refresh_rate))
        self.iren.AddObserver("TimerEvent", self.rotate)
        self.iren.Initialize()
        self.iren.Start()
        self.offset = None
        self.vtkWidget.installEventFilter(self)

        self.MistL1 = QLabel(self)
        self.MistL1.setStyleSheet("background-color: rgb(18,18,18)")
        self.MistL1.setFixedSize(30, 30)
        self.MistL1.move(5,5)
        self.MenuB = QPushButton(self)
        self.MenuB.setStyleSheet("background-color: rgb(0,128,255); border-radius : 15px;")
        self.MenuB.setFixedSize(30, 30)
        self.MenuB.move(5, 5)
        self.MenuB.clicked.connect(self.Menu)

        self.MistL2 = QLabel(self)
        self.MistL2.setStyleSheet("background-color: rgb(18,18,18)")
        self.MistL2.setFixedSize(30, 30)
        self.MistL2.move(266,5)
        self.end_x = QPushButton(self)
        self.end_x.setStyleSheet("background-color: rgb(255,0,127); border-radius : 15px;")
        self.end_x.setFixedSize(30, 30)
        self.end_x.clicked.connect(lambda: self.close())
        self.end_x.move(266, 5)

    def IRecord(self):

        self.worker = Recorder()
        self.thread2 = QThread()

        self.worker.moveToThread(self.thread2)
        self.worker.my_flag = True
        self.worker.phrase.connect(lambda phrase: print(phrase))

        self.thread2.started.connect(self.worker.record_to_file)

        self.worker.finished.connect(self.thread2.exit)

    def IAnimate(self):

        self.processingData_worker = ProcessingData()
        self.thread3 = QThread()

        self.processingData_worker.data_of_x_and_y.connect(lambda param1, param2: self.Light(param1, param2))

        self.processingData_worker.moveToThread(self.thread3)

        self.thread3.started.connect(self.processingData_worker.Update)

        self.processingData_worker.finished.connect(self.thread3.exit)

    def Light(self, data_x, data_y):
        y = np.average(data_y) ** 20 / 10**43
        self.shaders.GetFragmentCustomUniforms().SetUniformf("iTime", float(y))

    def rotate(self, caller, timer_event):
        self.actor.RotateY(0.12)
        self.vtkWidget.Render()

    def eventFilter(self, source, event):
        if source == self.vtkWidget:
            if event.type() == QEvent.MouseButtonPress:
                self.offset = event.pos()
            elif event.type() == QEvent.MouseMove and self.offset is not None:
                # no need for complex computations: just use the offset to compute
                # "delta" position, and add that to the current one
                self.move(self.pos() - self.offset + event.pos())
                # return True to tell Qt that the event has been accepted and
                # should not be processed any further
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.offset = None
        # let Qt process any other event
        return super().eventFilter(source, event)

    def Menu(self):
        self.sidebar = QLabel(self)
        self.sidebar.setFixedSize(50,500)
        self.sidebar.setStyleSheet("background-color: rgb(0,91,150)")
        self.btn = QPushButton(self.sidebar)
        self.btn.setFixedSize(50,50)
        self.btn.setStyleSheet("background-color: rgb(3,57,108); border: none")
        self.btn.clicked.connect(lambda: print("Clicked"))
        self.sidebar.show()
        self.MenuB.hide()
        self.ren.SetBackground([0.02,0.02,0.02])
        self.shaders.GetFragmentCustomUniforms().SetUniform3f("Color", [0.4,0.05,0.0])
        self.btn.setIcon(QIcon('resources/images/brainicon.png'))
        self.btn.setIconSize(QSize(50, 50))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    win.thread2.start()
    win.thread3.start()
    app.exec_()
    sys.exit()