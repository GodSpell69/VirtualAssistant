import sys
from PyQt5 import QtWidgets, QtCore
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
        #region ___Shaders___
        self.vec1 = '''//VTK::Normal::Dec
        varying vec3 myNormalMCVSOutput;
        '''
        self.vec2 = '''//VTK::Normal::Impl
        myNormalMCVSOutput = normalMC;
        '''
        self.frag1 = '''//VTK::Normal::Dec
        varying vec3 myNormalMCVSOutput;
        '''
        self.frag2 = '''//VTK::Normal::Impl
        diffuseColor = vec3(Color);
        ambientColor = abs(myNormalMCVSOutput*iTime);
        '''
        #endregion

        self.IDesign()
        self.IThreads()

    def IDesign(self):
        #region _____Create_Render_____
        self.screen_size = QApplication.primaryScreen().size()
        self.reader = vtk.vtkOBJReader()
        self.reader.SetFileName(r"resources\models\brain.obj")
        self.reader.Update()
        self.background = 0.02
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground([
        self.background,self.background,self.background])
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.camera = self.ren.GetActiveCamera()
        #endregion

        #region _________Axons_________
        self.edges = vtk.vtkExtractEdges()
        self.edges.SetInputConnection(self.reader.GetOutputPort())
        self.edges.Update()
        self.tube = vtk.vtkTubeFilter()
        self.tube.SetInputConnection(self.edges.GetOutputPort())
        self.tube.SetRadius(0.001)
        self.tube.SetNumberOfSides(6)
        self.tube.CappingOff()
        self.tube.Update()
        self.sphere = vtk.vtkSphereSource()
        self.sphere.SetRadius(0.002)
        self.glyph = vtk.vtkGlyph3D()
        self.glyph.SetInputConnection(self.edges.GetOutputPort())
        self.glyph.SetSourceConnection(self.sphere.GetOutputPort())
        self.glyph.SetVectorModeToUseNormal()
        self.glyph.Update()
        #endregion

        #region _________Nucleus_________
        self.sphere_mapper = vtkOpenGLPolyDataMapper()
        self.sphere_mapper.SetInputConnection(self.glyph.GetOutputPort())
        self.sphere_actor = vtkOpenGLActor()
        self.sphere_actor.SetMapper(self.sphere_mapper)
        self.sphere_actor.GetProperty().SetColor(0.020, 0.835, 0.886)
        self.sphere_actor.GetProperty().SetOpacity(0.5)
        self.sphere_actor.SetOrigin(-0.7230189442634583, 1.5103785395622253, 0.8213195204734802)
        self.sphere_actor.SetOrientation(0,90,0)
        self.sphere_actor.GetProperty().SetOpacity(0.0)
        #endregion

        #region ________Dendrites_________
        self.wireframe_mapper = vtkOpenGLPolyDataMapper()
        self.wireframe_mapper.SetInputConnection(self.tube.GetOutputPort())
        self.wireframe_actor = vtkOpenGLActor()
        self.wireframe_actor.SetMapper(self.wireframe_mapper)
        self.wireframe_actor.SetOrigin(-0.7230189442634583, 1.5103785395622253, 0.8213195204734802)
        self.wireframe_actor.GetProperty().SetOpacity(0.03)
        self.wireframe_actor.SetOrientation(0,90,0)
        self.wireframe_actor.GetProperty().SetOpacity(0.0)
        self.shaders = self.wireframe_actor.GetShaderProperty()
        self.shaders.GetFragmentCustomUniforms().SetUniformf("iTime", 0.1)
        self.shaders.GetFragmentCustomUniforms().SetUniform3f("Color", [0.020, 0.835, 0.886])
        self.shaders.AddVertexShaderReplacement(
            "//VTK::Normal::Dec", # replace the normal block
            True, # before the standard replacements
            self.vec1,
            #"gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;\n", #but we add this
            False # only do it once
        )
        self.shaders.AddVertexShaderReplacement(
            "//VTK::Normal::Impl", # replace the normal block
            True, # before the standard replacements
            self.vec2,
            False # only do it once
        )
        self.shaders.AddFragmentShaderReplacement(
            "//VTK::Normal::Dec", # replace the normal block
            True, # before the standard replacements
            self.frag1,
            False # only do it once
        )
        self.shaders.AddFragmentShaderReplacement(
            "//VTK::Normal::Impl", # replace the normal block
            True, # before the standard replacements
            self.frag2,
            False # only do it once
        )
        #endregion

        #region _________Countor_________
        self.hull_mapper = vtk.vtkPolyDataMapper()
        self.hull_mapper.SetInputConnection(self.reader.GetOutputPort())
        self.hull_actor = vtk.vtkActor()
        self.hull_actor.SetMapper(self.hull_mapper)
        self.hull_actor.GetProperty().SetColor(0.020, 0.835, 0.886)
        self.hull_actor.GetProperty().SetLighting(False)
        self.hull_actor.GetProperty().SetBackfaceCulling(False)
        self.hull_actor.SetOrientation(0,90,0)
        self.hull_actor.SetOrigin(-0.7230189442634583, 1.5103785395622253, 0.8213195204734802)
        self.hull_actor.GetProperty().SetOpacity(0)
        
        #endregion

        #region ______Config_Render_______
        self.ren.AddActor(self.wireframe_actor)
        self.ren.AddActor(self.sphere_actor)
        self.ren.AddActor(self.hull_actor)
        self.ren.ResetCamera()
        self.camera.Zoom(1.5)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.RemoveObservers(vtk.vtkCommand.LeftButtonPressEvent)
        self.iren.RemoveObservers(vtk.vtkCommand.RightButtonPressEvent)
        self.iren.RemoveObservers(vtk.vtkCommand.MiddleButtonPressEvent)
        self.iren.RemoveObservers(vtk.vtkCommand.MouseWheelForwardEvent)
        self.iren.RemoveObservers(vtk.vtkCommand.MouseWheelBackwardEvent)
        self.iren.Initialize()
        self.offset = None
         # Configuração da animação
        self.max_opacity_sphere = 0.5
        self.max_opacity_wireframe = 0.03
        self.max_opacity_hull = 0.01
        self.phase = 0  # 0 = fade in, 1 = fade out, 2 = fade in final, 3 = rotacionando
        self.opacity = 0.0
        self.rotation_angle = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.Animation)
        self.timer.start(16)  # 20 FPS
        #endregion

        #region _______Blue_Button________
        self.MistL1 = QLabel(self)
        self.MistL1.setStyleSheet("background-color: rgb(5,5,5)")
        self.MistL1.setFixedSize(30, 30)
        self.MenuB = QPushButton(self)
        self.MenuB.setStyleSheet("background-color: rgb(0,49,110); border-radius : 15px;")
        self.MenuB.setFixedSize(30, 30)
        self.MenuB.hide()
        self.MenuB.clicked.connect(self.OpenMenu)
        #endregion

        #region ________Mic_Toggle_________
        self.MistL2 = QLabel(self)
        self.MistL2.setStyleSheet("background-color: rgb(5,5,5)")
        self.MistL2.setFixedSize(30, 30)
        self.micAvaible = QPushButton(self)
        self.micAvaible.setStyleSheet("background-color: rgb(5,5,5); border-radius : 15px;")
        self.micAvaible.setFixedSize(30, 30)
        self.micAvaible.setIcon(QIcon('resources/images/micMute.png'))
        self.micAvaible.setIconSize(QSize(91,91))
        self.micAvaible.clicked.connect(self.Mic)
        #endregion

        #region _____Show______
        self.setWindowTitle("Jarvis")
        self.setMinimumSize(int(self.screen_size.width()/2.5),int(self.screen_size.height()/2.5))
        self.showMaximized()
        #endregion
        
    def IThreads(self):

        #region ____Mic____
        self.worker = Recorder()
        self.thread2 = QThread()

        self.worker.moveToThread(self.thread2)
        self.worker.record_flag = True
        self.worker.mic.connect(lambda param1: self.Mic(param1))

        self.thread2.started.connect(self.worker.record_to_file)

        self.worker.finished.connect(self.thread2.exit)
        #endregion

        #region ____Glow____
        self.processingData_worker = ProcessingData()
        self.thread3 = QThread()

        self.processingData_worker.data_of_y.connect(lambda param1: self.Glow(param1))

        self.processingData_worker.moveToThread(self.thread3)

        self.thread3.started.connect(self.processingData_worker.Update)

        self.processingData_worker.finished.connect(self.thread3.exit)
        #endregion

    def Glow(self, volume):
        y = np.average(volume) ** 20 / 10**43
        self.shaders.GetFragmentCustomUniforms().SetUniformf("iTime", float(y))

    def Animation(self):
        step = 0.015
        base_factor = 1/16
        self.wireframe_actor.RotateY(0.12)
        self.sphere_actor.RotateY(0.12)
        self.hull_actor.RotateY(0.12)
        if self.phase == 0:  # Fade in inicial
            value = self.background + (self.opacity * base_factor)
            self.hull_actor.GetProperty().SetOpacity(1)
            self.hull_actor.GetProperty().SetColor(value,value,value)
            self.opacity += step
            if self.opacity >= 1.0:
                self.opacity = 1.0
                self.phase = 1
        elif self.phase == 1:  # Fade out
            value = self.background + (self.opacity * base_factor)
            self.hull_actor.GetProperty().SetColor(value,value,value)
            self.opacity -= step
            if self.opacity <= 0.0:
                self.opacity = 0.0
                self.phase = 2
        elif self.phase == 2:  # Fade in final
            self.hull_actor.GetProperty().SetColor(0.020, 0.835, 0.886)
            self.hull_actor.GetProperty().SetOpacity(self.opacity * self.max_opacity_hull)
            self.sphere_actor.GetProperty().SetOpacity(self.opacity * self.max_opacity_sphere)
            self.wireframe_actor.GetProperty().SetOpacity(self.opacity * self.max_opacity_wireframe)
            self.opacity += step
            if self.opacity >= 1.0:
                self.opacity = 1.0
        self.vtkWidget.GetRenderWindow().Render()

    def OpenMenu(self):
        self.sidebar = QLabel(self)
        self.sidebar.setFixedSize(50,self.screen_size.height())
        self.sidebar.setStyleSheet("background-color: rgb(0,91,150)")
        self.btn = QPushButton(self.sidebar)
        self.btn.setFixedSize(50,50)
        self.btn.setStyleSheet("background-color: rgb(3,57,108); border: none")
        self.btn.clicked.connect(lambda: self.CloseMenu())
        self.sidebar.show()
        self.MistL1.hide()
        self.MistL2.hide()
        self.MenuB.hide()
        self.micAvaible.hide()
        self.ren.SetBackground([0.02,0.02,0.02])
        self.shaders.GetFragmentCustomUniforms().SetUniform3f("Color", [0.0,0.0,0.0])
        self.btn.setIcon(QIcon('resources/images/brainicon.png'))
        self.btn.setIconSize(QSize(50, 50))

    def CloseMenu(self):
        self.sidebar.hide()
        self.ren.SetBackground([0.07, 0.07, 0.07])
        self.shaders.GetFragmentCustomUniforms().SetUniform3f("Color", [0.0, 0.7176, 0.9216])
        self.MistL1.show()
        self.MistL2.show()
        self.MenuB.show()
        self.micAvaible.show()

    def Mic(self, state):
        if state == True:
            self.micAvaible.setIcon(QIcon('resources/images/micOn.png'))
            self.micAvaible.setIconSize(QSize(35,35))
        else:
            self.micAvaible.setIcon(QIcon('resources/images/micMute.png'))
            self.micAvaible.setIconSize(QSize(91, 91))

    def eventFilter(self, source, event):
        if source == self.vtkWidget:
            if event.type() == QEvent.MouseButtonPress:
                self.offset = event.pos()
            elif event.type() == QEvent.MouseMove and self.offset is not None:
                self.move(self.pos() - self.offset + event.pos())
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.offset = None
        return super().eventFilter(source, event)
    
    def resizeEvent(self, event):
        self.vtkWidget.resize(self.width(), self.height())
        self.MistL1.move(5, 5)
        self.MenuB.move(5, 5)
        self.MistL2.move(self.width() - 40, self.height() - 40)
        self.micAvaible.move(self.width() - 40, self.height() - 40)

        if hasattr(self, 'sidebar') and self.sidebar.isVisible():
            self.sidebar.setFixedHeight(self.height())


        self.vtkWidget.GetRenderWindow().Render()
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.thread2.start()
    win.thread3.start()
    sys.exit(app.exec_())