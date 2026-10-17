package
{
   import inq.hpold.battle.PlayerPanelsUI;
   import inq.hpold.injector.AbstractViewInjector;
   import inq.hpold.injector.IAbstractInjector;

   public class InqHpoldPanel extends AbstractViewInjector implements IAbstractInjector
   {
      public function InqHpoldPanel()
      {
         super();
      }

      override public function get componentUI():Class
      {
         return PlayerPanelsUI;
      }

      override public function get componentName():String
      {
         return "PlayerPanelsUI";
      }
   }
}
