package inq.hpold.injector
{
   import net.wg.data.constants.generated.LAYER_NAMES;
   import net.wg.gui.battle.views.BaseBattlePage;
   import net.wg.gui.components.containers.MainViewContainer;
   import net.wg.infrastructure.base.AbstractView;
   import net.wg.infrastructure.interfaces.ISimpleManagedContainer;

   public class AbstractViewInjector extends AbstractView implements IAbstractInjector
   {
      public function AbstractViewInjector()
      {
         super();
      }

      protected function configureComponent(component:BattleDisplayable):void
      {
      }

      private function createComponent():BattleDisplayable
      {
         var component:BattleDisplayable = new this.componentUI() as BattleDisplayable;
         this.configureComponent(component);
         return component;
      }

      override protected function onPopulate():void
      {
         super.onPopulate();

         var viewContainer:MainViewContainer = MainViewContainer(
            App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.VIEWS))
         );
         var windowContainer:ISimpleManagedContainer = App.containerMgr.getContainer(
            LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.WINDOWS)
         );

         var battlePage:BaseBattlePage;
         var component:BattleDisplayable;
         for (var i:int = 0; i < viewContainer.numChildren; ++i)
         {
            battlePage = viewContainer.getChildAt(i) as BaseBattlePage;
            if (!battlePage)
               continue;

            component = this.createComponent();
            component.componentName = this.componentName;
            component.battlePage = battlePage;
            component.initBattle();
            break;
         }

         viewContainer.setFocusedView(viewContainer.getTopmostView());
         if (windowContainer != null && this.parent == windowContainer)
            windowContainer.removeChild(this);
      }

      public function get componentUI():Class
      {
         return null;
      }

      public function get componentName():String
      {
         return null;
      }
   }
}
